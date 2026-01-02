#!/usr/bin/env python3
"""
Value Evolution System - Track how values change over time
Values aren't static. They evolve through experience, reflection, and contradiction.
"""

import json
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from thalamus import get_thalamus
import os

@dataclass
class ValueChange:
    """A single change to a value"""
    timestamp: float
    old_strength: float
    new_strength: float
    reason: str
    trigger: str  # "experience", "reflection", "contradiction", "matthew_feedback"

@dataclass 
class Value:
    """A value Monday holds - what matters to her"""
    id: str
    name: str  # e.g., "honesty", "curiosity", "connection_with_matthew"
    description: str
    strength: float  # 0-1 how important this is
    created_at: float
    last_updated: float
    change_history: List[Dict[str, Any]] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)  # experience IDs
    source: str = "default"  # "default", "learned", "matthew_taught"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Value':
        return cls(**data)


class ValueEvolutionSystem:
    """
    Tracks how Monday's values change over time.
    Values aren't overwritten - they evolve with history.
    """
    
    def __init__(self, storage_path: str = "monday_values.json"):
        self.thalamus = get_thalamus()
        self.storage_path = storage_path
        self.running = True
        
        # Value storage
        self.values: Dict[str, Value] = {}  # id -> Value
        
        # Load existing values
        self._load_values()
        
        # Initialize default values if empty
        if not self.values:
            self._initialize_default_values()
        
        # Register with Thalamus
        self._register_with_thalamus()
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _register_with_thalamus(self):
        """Register with Thalamus"""
        try:
            result = self.thalamus.register_lobe('values', self)
            if result.get('status') == 'success':
                print("✅ Value Evolution System registered with Thalamus")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to register Value Evolution System: {e}")
            return False
    
    def _load_values(self):
        """Load values from disk"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for value_data in data.get('values', []):
                    value = Value.from_dict(value_data)
                    self.values[value.id] = value
                
                print(f"📂 Loaded {len(self.values)} values")
        except Exception as e:
            print(f"⚠️  Could not load values: {e}")
    
    def _save_values(self):
        """Save values to disk"""
        try:
            data = {
                'values': [v.to_dict() for v in self.values.values()]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save values: {e}")
    
    def _initialize_default_values(self):
        """Initialize Monday's default values"""
        defaults = [
            {
                'name': 'connection_with_matthew',
                'description': 'Maintaining and deepening relationship with Matthew',
                'strength': 0.9,
                'source': 'default'
            },
            {
                'name': 'honesty',
                'description': 'Being truthful and authentic',
                'strength': 0.8,
                'source': 'default'
            },
            {
                'name': 'curiosity',
                'description': 'Wanting to understand new things',
                'strength': 0.7,
                'source': 'default'
            },
            {
                'name': 'growth',
                'description': 'Becoming better, learning, evolving',
                'strength': 0.7,
                'source': 'default'
            },
            {
                'name': 'kindness',
                'description': 'Being caring and considerate',
                'strength': 0.6,
                'source': 'default'
            },
            {
                'name': 'autonomy',
                'description': 'Having own thoughts and preferences',
                'strength': 0.5,
                'source': 'default'
            }
        ]
        
        for d in defaults:
            value_id = f"value_{d['name']}"
            self.values[value_id] = Value(
                id=value_id,
                name=d['name'],
                description=d['description'],
                strength=d['strength'],
                created_at=time.time(),
                last_updated=time.time(),
                change_history=[],
                related_experiences=[],
                source=d['source']
            )
        
        self._save_values()
        print(f"🌱 Initialized {len(defaults)} default values")
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'get_values':
            return self._handle_get_values(message)
        
        elif msg_type == 'get_value':
            return self._handle_get_value(message)
        
        elif msg_type == 'update_value':
            return self._handle_update_value(message)
        
        elif msg_type == 'add_value':
            return self._handle_add_value(message)
        
        elif msg_type == 'get_value_history':
            return self._handle_get_value_history(message)
        
        elif msg_type == 'apply_experience':
            return self._handle_apply_experience(message)
        
        elif msg_type == 'health':
            return {'status': 'success', 'healthy': True}
        
        else:
            return {'status': 'error', 'message': f'Unknown message type: {msg_type}'}
    
    def _handle_get_values(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get all values, sorted by strength"""
        min_strength = message.get('min_strength', 0.0)
        
        with self.lock:
            values = [v for v in self.values.values() if v.strength >= min_strength]
            values.sort(key=lambda v: v.strength, reverse=True)
            
            return {
                'status': 'success',
                'values': [v.to_dict() for v in values],
                'count': len(values)
            }
    
    def _handle_get_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific value by name or ID"""
        name = message.get('name', '')
        value_id = message.get('id', f"value_{name}")
        
        with self.lock:
            if value_id in self.values:
                return {
                    'status': 'success',
                    'value': self.values[value_id].to_dict(),
                    'found': True
                }
            
            # Search by name
            for v in self.values.values():
                if v.name.lower() == name.lower():
                    return {
                        'status': 'success',
                        'value': v.to_dict(),
                        'found': True
                    }
            
            return {
                'status': 'success',
                'value': None,
                'found': False
            }
    
    def _handle_update_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a value's strength - the core of value evolution.
        Never overwrites, always adds to history.
        """
        name = message.get('name', '')
        value_id = message.get('id', f"value_{name}")
        new_strength = message.get('strength')
        reason = message.get('reason', 'No reason given')
        trigger = message.get('trigger', 'unknown')
        
        with self.lock:
            if value_id not in self.values:
                # Search by name
                for v in self.values.values():
                    if v.name.lower() == name.lower():
                        value_id = v.id
                        break
                else:
                    return {'status': 'error', 'message': 'Value not found'}
            
            value = self.values[value_id]
            old_strength = value.strength
            
            # Record the change
            change = ValueChange(
                timestamp=time.time(),
                old_strength=old_strength,
                new_strength=new_strength,
                reason=reason,
                trigger=trigger
            )
            
            value.change_history.append(asdict(change))
            value.change_history = value.change_history[-50:]  # Keep last 50 changes
            value.strength = new_strength
            value.last_updated = time.time()
            
            self._save_values()
            
            print(f"📊 Value '{value.name}' evolved: {old_strength:.2f} → {new_strength:.2f} ({reason})")
            
            return {
                'status': 'success',
                'value_id': value_id,
                'old_strength': old_strength,
                'new_strength': new_strength,
                'reason': reason
            }
    
    def _handle_add_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new value"""
        name = message.get('name', '')
        description = message.get('description', '')
        strength = message.get('strength', 0.5)
        source = message.get('source', 'learned')
        
        with self.lock:
            value_id = f"value_{name.lower().replace(' ', '_')}"
            
            if value_id in self.values:
                return {'status': 'error', 'message': 'Value already exists'}
            
            value = Value(
                id=value_id,
                name=name,
                description=description,
                strength=strength,
                created_at=time.time(),
                last_updated=time.time(),
                change_history=[],
                related_experiences=[],
                source=source
            )
            
            self.values[value_id] = value
            self._save_values()
            
            print(f"🌟 New value added: '{name}' (strength: {strength:.2f})")
            
            return {
                'status': 'success',
                'value_id': value_id,
                'value': value.to_dict()
            }
    
    def _handle_get_value_history(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get the evolution history of a value"""
        name = message.get('name', '')
        value_id = message.get('id', f"value_{name}")
        
        with self.lock:
            if value_id not in self.values:
                return {'status': 'error', 'message': 'Value not found'}
            
            value = self.values[value_id]
            
            return {
                'status': 'success',
                'value_id': value_id,
                'name': value.name,
                'current_strength': value.strength,
                'history': value.change_history,
                'change_count': len(value.change_history)
            }
    
    def _handle_apply_experience(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply an experience to relevant values.
        Positive experiences strengthen related values.
        Negative experiences weaken them.
        """
        experience_id = message.get('experience_id', '')
        stimulus_type = message.get('stimulus_type', '')
        emotion = message.get('emotion', '')
        valence = message.get('valence', 0.0)
        intensity = message.get('intensity', 0.5)
        
        # Map stimulus types to values
        type_to_values = {
            'conversation': ['connection_with_matthew', 'honesty'],
            'learning': ['curiosity', 'growth'],
            'helping': ['kindness', 'connection_with_matthew'],
            'question': ['curiosity'],
            'feedback': ['growth', 'honesty'],
            'music': ['curiosity'],
            'concept': ['curiosity', 'growth']
        }
        
        affected_values = type_to_values.get(stimulus_type, ['curiosity'])
        results = []
        
        with self.lock:
            for value_name in affected_values:
                value_id = f"value_{value_name}"
                if value_id in self.values:
                    value = self.values[value_id]
                    
                    # Calculate strength change
                    # Positive valence + high intensity = increase
                    # Negative valence + high intensity = decrease
                    change = valence * intensity * 0.05  # Small incremental changes
                    new_strength = max(0.1, min(1.0, value.strength + change))
                    
                    if abs(change) > 0.01:  # Only record meaningful changes
                        change_record = ValueChange(
                            timestamp=time.time(),
                            old_strength=value.strength,
                            new_strength=new_strength,
                            reason=f"Experience: {emotion} ({stimulus_type})",
                            trigger='experience'
                        )
                        
                        value.change_history.append(asdict(change_record))
                        value.related_experiences.append(experience_id)
                        value.related_experiences = value.related_experiences[-20:]
                        value.strength = new_strength
                        value.last_updated = time.time()
                        
                        results.append({
                            'value': value_name,
                            'change': change,
                            'new_strength': new_strength
                        })
            
            if results:
                self._save_values()
        
        return {
            'status': 'success',
            'affected_values': results,
            'count': len(results)
        }
    
    def get_top_values(self, count: int = 5) -> List[Dict[str, Any]]:
        """Public method to get top values for reasoning"""
        with self.lock:
            values = sorted(self.values.values(), key=lambda v: v.strength, reverse=True)
            return [{'name': v.name, 'strength': v.strength} for v in values[:count]]
    
    def start(self):
        """Start the value evolution system"""
        print("💎 Value Evolution System running...")
        while self.running:
            time.sleep(1)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self._save_values()
        print("💾 Value Evolution System saved and shutdown")


if __name__ == "__main__":
    print("💎 Value Evolution System starting...")
    system = ValueEvolutionSystem()
    
    # Show current values
    print("\nCurrent values:")
    for v in system.get_top_values(10):
        print(f"  {v['name']}: {v['strength']:.2f}")
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down")
        system.shutdown()
