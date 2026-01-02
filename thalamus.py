#!/usr/bin/env python3
"""
Thalamus - Message Router with Request-Response Support
Routes messages between lobes with message IDs, waiting, and timeouts
No memory, no coordination, just routing
"""

import json
import os
import time
import threading
import uuid
import sys
from queue import Queue, Empty
from typing import Dict, List, Any, Set, Optional, Tuple, Callable
from collections import defaultdict
from dataclasses import dataclass, asdict

# Global singleton instance
_thalamus_instance = None

@dataclass
class LobMessage:
    """Standardized message format for inter-lobe communication"""
    id: str  # Unique message ID for tracking
    source: str
    destination: str
    msg_type: str
    content: Dict[str, Any]
    timestamp: float = None
    response_to: str = None  # If this is a response, which message ID is it responding to
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LobMessage':
        """Create from dictionary"""
        return cls(**data)

class Thalamus:
    def send_message(self, destination: str, msg_type: str, content: dict, source: str = None, message_id: str = None) -> dict:
        """
        Synchronous message send: routes message to the destination lobe and returns the result.
        Enforces canonical message schema and direct function call (no sockets).
        """
        if message_id is None:
            message_id = self._generate_message_id()
        # Canonicalize content
        canonical_content = content.copy() if isinstance(content, dict) else {'value': content}
        for k in ('type', 'source', 'destination', '_message_id'):
            canonical_content.pop(k, None)
        # Canonical message format
        message = {
            'type': msg_type,
            '_message_id': message_id,
            'content': canonical_content
        }
        # Route to lobe handler
        with self.lobe_handlers_lock:
            lobe_handler = self.lobe_handlers.get(destination)
            if not lobe_handler:
                self.lobe_status[destination] = "offline"
                return {'status': 'error', 'message': f'{destination} is not registered with Thalamus', 'message_id': message_id}
        try:
            self._set_message_state(message_id, 'processing')
            if hasattr(lobe_handler, 'process_message'):
                result = lobe_handler.process_message(message)
            elif hasattr(lobe_handler, 'handle_request'):
                result = lobe_handler.handle_request(message)
            else:
                result = {'status': 'error', 'message': f'{destination} has no process_message or handle_request method'}
            result['message_id'] = message_id
            if result.get('status') == 'success':
                transformed_content = self.transform_output(destination, result.get('content', result))
                result['content'] = transformed_content
            self.lobe_status[destination] = "online"
            self.lobe_last_response[destination] = time.time()
            self._set_message_state(message_id, 'complete')
            return result
        except Exception as e:
            self.lobe_status[destination] = "error"
            self._set_message_state(message_id, 'error')
            return {'status': 'error', 'message': f'{destination}: {str(e)}', 'message_id': message_id}
    
    def __init__(self, config_path="thalamus_config.json"):
        global _thalamus_instance
        _thalamus_instance = self
        self.running = True
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # List of expected lobes (they connect to us as clients)
        self.expected_lobes = [
            "notus", "emotion", "perception", "reasoning", "output",
            "pattern", "representation", "conversation", "language", "voice", "novelty",
            "attention", "motor_action", "executive_control", "meta_cognition",
            "social_context", "sensory_integration", "value_goal_management"
        ]
        
        self.lobe_status = {lobe: "unknown" for lobe in self.expected_lobes}
        
        # Direct function references from lobes (NO SOCKETS)
        self.lobe_handlers = {}  # {lobe_name: lobe_instance}
        self.lobe_handlers_lock = threading.Lock()
        
        # === NEW: Request-Response System ===
        self.pending_responses = {}  # {message_id: response}
        self.response_events = {}    # {message_id: threading.Event}
        self.response_lock = threading.Lock()
        
        # === NEW: Message Queues for Async ===
        self.lobe_queues = {lobe: Queue() for lobe in self.expected_lobes}
        
        # === NEW: Message State Tracking ===
        self.message_states = {}  # {message_id: 'sent' | 'received' | 'processing' | 'complete'}
        self.message_states_lock = threading.Lock()
        
        # === NEW: Lobe Health Tracking ===
        self.lobe_last_response = {lobe: 0.0 for lobe in self.expected_lobes}
        self.lobe_health_timeout = 10.0  # seconds before marking unhealthy
        
        # Translation mappings - convert lobe-specific formats to standard LobMessage
        self.format_translators = {
            'perception': self._translate_perception_output,
            'notus': self._translate_notus_output,
            'emotion': self._translate_emotion_output,
            'reasoning': self._translate_reasoning_output,
            'language': self._translate_language_output,
            'pattern': self._translate_pattern_output,
            'conversation': self._translate_conversation_output,
            'voice': self._translate_voice_output,
            'novelty': self._translate_novelty_output,
        }
        
        # Restricted communication paths - only these paths are allowed
        self.allowed_paths = {
            'perception': ['reasoning', 'novelty', 'attention', 'sensory_integration'],
            'notus': ['reasoning', 'novelty', 'executive_control'],
            'emotion': ['reasoning', 'novelty', 'meta_cognition'],
            'pattern': ['reasoning', 'novelty', 'attention'],
            'reasoning': ['notus', 'language', 'novelty', 'executive_control', 'value_goal_management'],
            'novelty': ['notus', 'language', 'attention'],
            'language': ['output', 'social_context'],
            'output': ['gui', 'motor_action'],
            'attention': ['reasoning', 'perception', 'pattern', 'executive_control'],
            'motor_action': ['output', 'executive_control'],
            'executive_control': ['reasoning', 'motor_action', 'attention', 'value_goal_management'],
            'meta_cognition': ['executive_control', 'reasoning', 'emotion'],
            'social_context': ['language', 'output', 'reasoning'],
            'sensory_integration': ['perception', 'attention'],
            'value_goal_management': ['executive_control', 'reasoning']
        }
    
    def _translate_perception_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform perception lobe output to standard format"""
        # Perception outputs: text, confidence, intent_hints, entities
        return {
            'text': content.get('text', ''),
            'confidence': content.get('confidence', 0.0),
            'intent_hints': content.get('intent_hints', []),
            'entities': content.get('entities', []),
            'timestamp': content.get('timestamp', time.time())
        }
    
    def _translate_notus_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform notus (memory) lobe output to standard format"""
        # Notus outputs: memories, facts, patterns, embeddings
        return {
            'memories': content.get('memories', []),
            'facts': content.get('facts', []),
            'patterns': content.get('patterns', []),
            'embeddings': content.get('embeddings', []),
            'query_results': content.get('query_results', [])
        }
    
    def _translate_emotion_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform emotional engine output to standard format"""
        # Emotional engine outputs: PAD values, emotional state, arousal level
        return {
            'pleasure': content.get('pleasure', 0.5),
            'arousal': content.get('arousal', 0.5),
            'dominance': content.get('dominance', 0.5),
            'emotional_state': content.get('emotional_state', 'neutral'),
            'intensity': content.get('intensity', 0.5),
            'needs': content.get('needs', {}),
            'attachment': content.get('attachment', {})
        }
    
    def _translate_reasoning_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform reasoning lobe output to standard format"""
        # Reasoning outputs: thoughts, decisions, next_action, internal_state
        return {
            'thoughts': content.get('thoughts', []),
            'decision': content.get('decision', ''),
            'confidence': content.get('confidence', 0.0),
            'next_action': content.get('next_action', None),
            'internal_state': content.get('internal_state', {}),
            'context_used': content.get('context_used', [])
        }
    
    def _translate_language_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform language generation output to standard format"""
        # Language gen outputs: text, grammar_used, vocabulary_items, emotional_tone
        return {
            'text': content.get('text', ''),
            'grammar_rule': content.get('grammar_rule', ''),
            'vocabulary': content.get('vocabulary', []),
            'emotional_tone': content.get('emotional_tone', 'neutral'),
            'emphasis': content.get('emphasis', [])
        }
    
    def _translate_pattern_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pattern recognition output to standard format"""
        # Pattern outputs: patterns_found, confidence, implications
        return {
            'patterns': content.get('patterns', []),
            'pattern_type': content.get('pattern_type', ''),
            'confidence': content.get('confidence', 0.0),
            'implications': content.get('implications', [])
        }
    
    def _translate_conversation_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform conversation lobe output to standard format"""
        # Conversation outputs: intent, entities, sentiment, topic
        return {
            'intent': content.get('intent', 'statement'),
            'entities': content.get('entities', []),
            'sentiment': content.get('sentiment', 'neutral'),
            'topic': content.get('topic', ''),
            'confidence': content.get('confidence', 0.0)
        }
    
    def _translate_voice_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform voice lobe output to standard format"""
        # Voice outputs: audio, voice_profile, prosody
        return {
            'audio': content.get('audio', None),
            'voice_profile': content.get('voice_profile', 'Monday'),
            'pitch': content.get('pitch', 1.0),
            'speed': content.get('speed', 1.0),
            'warmth': content.get('warmth', 0.5),
            'confidence': content.get('confidence', 1.0)
        }
    
    def _translate_novelty_output(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Transform novelty lobe output to standard format"""
        # Novelty outputs: stimulus, question, emotion
        return {
            'stimulus': content.get('stimulus', ''),
            'question': content.get('question', ''),
            'emotion': content.get('emotion', 'curious'),
            'intensity': content.get('intensity', 0.5),
            'confidence': content.get('confidence', 0.5)
        }
    
    def transform_output(self, source: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize output from any lobe to consistent format using translators if available."""
        translator = self.format_translators.get(source)
        if translator:
            return translator(content)
        else:
            print(f"⚠️  No translator for lobe '{source}', passing content as-is.")
            return content
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('thalamus', {})
        except Exception as e:
            print(f"⚠️  Could not load config: {e}, using defaults")
        return {}
    
    
    
    def register_lobe(self, lobe_name: str, lobe_instance: Any) -> Dict[str, Any]:
        """Register a lobe with direct function reference (NO SOCKETS)"""
        with self.lobe_handlers_lock:
            self.lobe_handlers[lobe_name] = lobe_instance
            self.lobe_status[lobe_name] = "online"
            self.lobe_last_response[lobe_name] = time.time()
            print(f"✅ {lobe_name} registered with Thalamus (direct function calls)")
        return {'status': 'success', 'message': 'Registered'}
    
    # === NEW: Generate unique message ID ===
    def _generate_message_id(self) -> str:
        """Generate a unique message ID"""
        return str(uuid.uuid4())
    
    # === NEW: Track message state ===
    def _set_message_state(self, message_id: str, state: str):
        """Set the state of a message (sent, received, processing, complete)"""
        with self.message_states_lock:
            self.message_states[message_id] = state
    
    def _get_message_state(self, message_id: str) -> str:
        """Get the state of a message"""
        with self.message_states_lock:
            return self.message_states.get(message_id, 'unknown')
    
    # === NEW: Wait for response ===
    def wait_for_response(self, message_id: str, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Block until a response arrives for the given message ID.
        Returns the response or {'status': 'timeout'} if timeout exceeded.
        """
        event = threading.Event()
        
        with self.response_lock:
            # Check if response already arrived
            if message_id in self.pending_responses:
                response = self.pending_responses.pop(message_id)
                return response
            # Otherwise set up wait
            self.response_events[message_id] = event
        
        # Wait for response
        if event.wait(timeout):
            with self.response_lock:
                if message_id in self.pending_responses:
                    response = self.pending_responses.pop(message_id)
                    if message_id in self.response_events:
                        del self.response_events[message_id]
                    return response
        
        # Timeout
        with self.response_lock:
            if message_id in self.response_events:
                del self.response_events[message_id]
        return {'status': 'timeout', 'message': f'No response after {timeout}s'}
    
    # === NEW: Register a response ===
    def register_response(self, message_id: str, response: Dict[str, Any]):
        """
        Register a response to a message. Unblocks any wait_for_response() calls.
        """
        with self.response_lock:
            self.pending_responses[message_id] = response
            if message_id in self.response_events:
                self.response_events[message_id].set()
        self._set_message_state(message_id, 'complete')
    
    # === NEW: Send and wait ===
    def send_and_wait(self, destination: str, msg_type: str, content: Dict[str, Any], 
                      source: str = None, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Send a message and wait for the response.
        This is the primary method for request-response communication.
        """
        message_id = self._generate_message_id()
        
        # Add message ID to content so receiver can respond to it
        content_with_id = {**content, '_message_id': message_id}
        
        # Send the message
        result = self.send_message(destination, msg_type, content_with_id, source, message_id)
        
        # If synchronous call already got result, return it
        if result.get('status') in ['success', 'error']:
            return result
        
        # Otherwise wait for async response
        return self.wait_for_response(message_id, timeout)
    
    # === NEW: Send async (fire and forget with tracking) ===
    def send_message_async(self, destination: str, msg_type: str, content: Dict[str, Any], 
                           source: str = None) -> str:
        """
        Send a message asynchronously. Returns message ID for tracking.
        Use wait_for_response(message_id) later to get the response.
        """
        message_id = self._generate_message_id()
        content_with_id = {**content, '_message_id': message_id}
        
        # Queue the message for the destination lobe
        if destination in self.lobe_queues:
            message = {
                'id': message_id,
                'type': msg_type,
                'source': source,
                'content': content_with_id
            }
            self.lobe_queues[destination].put(message)
            self._set_message_state(message_id, 'sent')
        
        return message_id
    
    # === NEW: Get queued messages for a lobe ===
    def get_queued_messages(self, lobe_name: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Get queued messages for a lobe. Called by lobes to pull their messages.
        """
        messages = []
        if lobe_name in self.lobe_queues:
            queue = self.lobe_queues[lobe_name]
            for _ in range(max_messages):
                try:
                    msg = queue.get_nowait()
                    messages.append(msg)
                    self._set_message_state(msg.get('id', ''), 'received')
                except Empty:
                    break
        return messages
    
    def broadcast_message(self, destinations: List[str], msg_type: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """Broadcast message to multiple lobes in parallel (one-way, fire-and-forget)"""
        import threading
        
        results = {'success': [], 'failed': []}
        result_lock = threading.Lock()
        
        def send_to_lobe(dest: str):
            """Send to a single lobe"""
            try:
                result = self.send_message(dest, msg_type, content)
                with result_lock:
                    if result.get('status') == 'success':
                        results['success'].append(dest)
                    else:
                        results['failed'].append(dest)
            except Exception:
                with result_lock:
                    results['failed'].append(dest)
        
        # Send to all destinations in parallel
        threads = []
        for dest in destinations:
            if dest in self.expected_lobes:
                thread = threading.Thread(target=send_to_lobe, args=(dest,), daemon=True)
                thread.start()
                threads.append(thread)
        
        # Don't wait for threads - fire and forget (one-way broadcast)
        return {'status': 'success', 'broadcast_to': destinations, 'results': results}
    
    
    
    def handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming requests"""
        msg_type = message.get('type')
        
        if msg_type == 'process_input':
            # Thalamus only routes messages - this should be handled by the calling code
            return {'status': 'error', 'message': 'Thalamus only routes messages, use send_message to communicate with lobes'}
        
        elif msg_type == 'check_autonomous':
            # Check for autonomous messages
            result = self.send_message("reasoning", "get_autonomous_actions", {})
            if result.get('status') == 'success':
                actions = result.get('actions', [])
                for action in actions:
                    if action.get('type') == 'message' and action.get('target') == 'matthew':
                        return {
                            'status': 'success',
                            'autonomous_message': action.get('content', '')
                        }
            return {'status': 'success', 'autonomous_message': None}
        
        elif msg_type == 'health':
            # Check all registered lobes
            with self.lobe_handlers_lock:
                for lobe_name in self.lobe_handlers.keys():
                    self.send_message(lobe_name, 'health', {})
            
            all_online = all(s == "online" for s in self.lobe_status.values())
            
            return {
                'status': 'success',
                'thalamus_healthy': True,
                'lobes': self.lobe_status,
                'all_lobes_online': all_online
            }
        
        elif msg_type == 'get_status':
            # Get current system status
            return {
                'status': 'success',
                'lobes': self.lobe_status,
                'message': 'Thalamus is a message router only - no health monitoring'
            }
        
        elif msg_type == 'get_monday_state':
            # Thalamus doesn't store memory - route to Notus or Reasoning
            return {'status': 'error', 'message': 'Thalamus does not store memory'}
        
        elif msg_type == 'who_are_you':
            # Thalamus doesn't store memory - route to Notus or Reasoning
            return {'status': 'error', 'message': 'Thalamus does not store memory'}
        
        elif msg_type == 'user_typing':
            # Forward user typing status to reasoning lobe
            is_typing = message.get('is_typing', False)
            self.send_message("reasoning", "user_typing", {
                'is_typing': is_typing
            })
            return {'status': 'success'}
        
        elif msg_type == 'query_notus':
            # Route Notus query from other lobes through Thalamus (prevents connection storms)
            notus_msg_type = message.get('notus_msg_type')
            notus_content = message.get('notus_content', {})
            if notus_msg_type:
                notus_result = self.send_message("notus", notus_msg_type, notus_content)
                return {
                    'status': 'success',
                    'notus_response': notus_result
                }
            else:
                return {'status': 'error', 'message': 'Missing notus_msg_type'}
        
        elif msg_type == 'route_message':
            # Route message from one lobe to another through Thalamus (for all inter-lobe communication)
            destination = message.get('destination')
            route_msg_type = message.get('msg_type')
            route_content = message.get('content', {})
            source = message.get('_source')  # Get source from message (set by connection handler)
            if destination and route_msg_type:
                result = self.send_message(destination, route_msg_type, route_content, source=source)
                return result
            else:
                return {'status': 'error', 'message': 'Missing destination or msg_type'}
        
        elif msg_type == 'broadcast_message':
            # Broadcast message to multiple lobes through Thalamus
            destinations = message.get('destinations', [])
            broadcast_msg_type = message.get('msg_type')
            broadcast_content = message.get('content', {})
            if destinations and broadcast_msg_type:
                result = self.broadcast_message(destinations, broadcast_msg_type, broadcast_content)
                return result
            else:
                return {'status': 'error', 'message': 'Missing destinations or msg_type'}
        
        else:
            return {'status': 'error', 'message': f'Unknown type: {msg_type}'}
    
    def start(self):
        """Start Thalamus - NO SOCKETS, DIRECT FUNCTION CALLS ONLY"""
        print("✅ Thalamus ready (direct function calls, NO SOCKETS)")
        print("🔌 Waiting for lobes to register...")
        
        print(f"""
╔════════════════════════════════════════╗
║        THALAMUS - Message Router       ║
║      DIRECT FUNCTION CALLS ONLY        ║
╚════════════════════════════════════════╝

📡 Message Router Only
   Communication: Direct function calls (NO SOCKETS)
   No memory, no coordination, just routing messages
   
🔌 Waiting for lobes to register:
   • Conversation
   • Reasoning
   • Language
   • Output
   • Voice
   • Memory (Notus)
   • Emotion
   • Perception
   • Pattern
   • Representation\n""")
        
        # Keep running (lobes call us directly, no accept loop needed)
        while self.running:
            time.sleep(1)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        print("\n🛑 Thalamus shutting down...")

def get_thalamus():
    """Get the global Thalamus instance"""
    global _thalamus_instance
    if _thalamus_instance is None:
        _thalamus_instance = Thalamus()
    return _thalamus_instance

if __name__ == "__main__":
    thalamus = Thalamus()
    try:
        thalamus.start()
    except KeyboardInterrupt:
        thalamus.shutdown()
    except Exception as e:
        print(f"\n❌ Thalamus crashed: {e}")
        import traceback
        traceback.print_exc()
        thalamus.shutdown()
        sys.exit(1)
