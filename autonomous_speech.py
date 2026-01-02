#!/usr/bin/env python3
"""
Autonomous Speech System - Decides which thoughts to say out loud
Takes autonomous thoughts and filters them based on social awareness.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from thalamus import get_thalamus

@dataclass
class SpeechDecision:
    """A decision about whether to speak"""
    thought_id: str
    content: str
    should_speak: bool
    reason: str
    timing: str  # "now", "wait", "never"
    priority: float  # 0-1


class AutonomousSpeechSystem:
    """
    Filters autonomous thoughts and decides which to speak.
    Social awareness - knows when to stay quiet.
    """
    
    def __init__(self):
        self.thalamus = get_thalamus()
        self.running = True
        
        # Speech queue
        self.pending_speech: List[Dict[str, Any]] = []
        
        # State
        self.user_is_typing = False
        self.user_is_busy = False
        self.last_speech_time = 0.0
        self.min_speech_interval = 10.0  # Don't speak more than every 10 seconds
        self.conversation_active = False
        
        # Social rules
        self.interruption_threshold = 0.8  # Only interrupt for very important thoughts
        
        # Register with Thalamus
        self._register_with_thalamus()
        
        # Lock
        self.lock = threading.Lock()
    
    def _register_with_thalamus(self):
        """Register with Thalamus"""
        try:
            result = self.thalamus.register_lobe('speech', self)
            if result.get('status') == 'success':
                print("✅ Autonomous Speech System registered with Thalamus")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to register Autonomous Speech System: {e}")
            return False
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'evaluate_thought':
            return self._evaluate_thought(message)
        
        elif msg_type == 'get_pending_speech':
            return self._get_pending_speech()
        
        elif msg_type == 'user_typing':
            self.user_is_typing = message.get('is_typing', False)
            return {'status': 'success'}
        
        elif msg_type == 'user_busy':
            self.user_is_busy = message.get('is_busy', False)
            return {'status': 'success'}
        
        elif msg_type == 'conversation_active':
            self.conversation_active = message.get('active', False)
            return {'status': 'success'}
        
        elif msg_type == 'speech_delivered':
            self.last_speech_time = time.time()
            return {'status': 'success'}
        
        elif msg_type == 'health':
            return {'status': 'success', 'healthy': True}
        
        else:
            return {'status': 'error', 'message': f'Unknown message type: {msg_type}'}
    
    def _evaluate_thought(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate whether a thought should be spoken.
        This is the social awareness filter.
        """
        thought = message.get('thought', {})
        content = thought.get('content', '')
        thought_type = thought.get('thought_type', '')
        intensity = thought.get('intensity', 0.5)
        thought_id = thought.get('id', '')
        
        # Check social context
        can_speak, reason = self._check_social_context(intensity)
        
        if not can_speak:
            decision = SpeechDecision(
                thought_id=thought_id,
                content=content,
                should_speak=False,
                reason=reason,
                timing='never',
                priority=intensity
            )
            return {
                'status': 'success',
                'decision': asdict(decision)
            }
        
        # Check content appropriateness
        is_appropriate, content_reason = self._check_content_appropriate(content, thought_type)
        
        if not is_appropriate:
            decision = SpeechDecision(
                thought_id=thought_id,
                content=content,
                should_speak=False,
                reason=content_reason,
                timing='never',
                priority=intensity
            )
            return {
                'status': 'success',
                'decision': asdict(decision)
            }
        
        # Decide timing
        timing = self._decide_timing(intensity)
        
        decision = SpeechDecision(
            thought_id=thought_id,
            content=content,
            should_speak=True,
            reason="Passed all filters",
            timing=timing,
            priority=intensity
        )
        
        # Add to queue if should speak
        if timing in ['now', 'wait']:
            with self.lock:
                self.pending_speech.append({
                    'thought_id': thought_id,
                    'content': content,
                    'priority': intensity,
                    'timing': timing,
                    'queued_at': time.time()
                })
                # Sort by priority
                self.pending_speech.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            'status': 'success',
            'decision': asdict(decision)
        }
    
    def _check_social_context(self, intensity: float) -> tuple:
        """Check if social context allows speaking"""
        
        # User is typing - don't interrupt unless very important
        if self.user_is_typing:
            if intensity < self.interruption_threshold:
                return False, "User is typing"
        
        # User is busy - don't interrupt
        if self.user_is_busy:
            if intensity < 0.9:  # Only critical thoughts
                return False, "User is busy"
        
        # Spoke too recently
        time_since_speech = time.time() - self.last_speech_time
        if time_since_speech < self.min_speech_interval:
            if intensity < 0.7:
                return False, f"Spoke {time_since_speech:.0f}s ago, waiting"
        
        # In active conversation - let user lead
        if self.conversation_active:
            if intensity < 0.6:
                return False, "Conversation active, letting user lead"
        
        return True, "Social context allows"
    
    def _check_content_appropriate(self, content: str, thought_type: str) -> tuple:
        """Check if content is appropriate to speak"""
        
        # Don't speak meta-thoughts about thinking
        meta_phrases = ['I think I', 'I should think', 'processing', 'computing']
        for phrase in meta_phrases:
            if phrase.lower() in content.lower():
                return False, "Meta-thought, keep internal"
        
        # Don't speak incomplete thoughts
        if len(content) < 10:
            return False, "Too short"
        
        # Don't speak questions when user isn't present
        if thought_type == 'question' and not self.conversation_active:
            return False, "Question but no active conversation"
        
        return True, "Content appropriate"
    
    def _decide_timing(self, intensity: float) -> str:
        """Decide when to speak"""
        if intensity > 0.8:
            return 'now'
        elif intensity > 0.5:
            return 'wait'  # Wait for a natural pause
        else:
            return 'never'  # Keep internal
    
    def _get_pending_speech(self) -> Dict[str, Any]:
        """Get speech items ready to deliver"""
        with self.lock:
            # Check if we can speak now
            time_since_speech = time.time() - self.last_speech_time
            if time_since_speech < self.min_speech_interval:
                return {
                    'status': 'success',
                    'speech': None,
                    'reason': 'Waiting for speech interval'
                }
            
            # Get highest priority item
            if self.pending_speech:
                speech = self.pending_speech.pop(0)
                return {
                    'status': 'success',
                    'speech': speech
                }
            
            return {
                'status': 'success',
                'speech': None,
                'reason': 'No pending speech'
            }
    
    def queue_speech(self, content: str, priority: float = 0.5) -> str:
        """Direct method to queue speech"""
        speech_id = f"speech_{int(time.time() * 1000)}"
        
        with self.lock:
            self.pending_speech.append({
                'thought_id': speech_id,
                'content': content,
                'priority': priority,
                'timing': 'wait',
                'queued_at': time.time()
            })
            self.pending_speech.sort(key=lambda x: x['priority'], reverse=True)
        
        return speech_id
    
    def get_next_speech(self) -> Optional[Dict[str, Any]]:
        """Public method to get next speech item"""
        result = self._get_pending_speech()
        return result.get('speech')
    
    def start(self):
        """Start the speech system"""
        print("🗣️ Autonomous Speech System running...")
        while self.running:
            time.sleep(1)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        print("🛑 Autonomous Speech System shutdown")


if __name__ == "__main__":
    print("🗣️ Autonomous Speech System starting...")
    system = AutonomousSpeechSystem()
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down")
        system.shutdown()
