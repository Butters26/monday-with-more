#!/usr/bin/env python3
"""
Value System Learning - Values emerge from experience
Values change through contradiction and reflection.
Develops independent goals.
"""

import json
import time
import threading
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from thalamus import get_thalamus

@dataclass
class EmergentValue:
    """A value that emerged from experience"""
    id: str
    name: str
    description: str
    strength: float  # 0-1 how important
    origin: str  # "seeded", "experience", "reflection", "contradiction"
    origin_experience: Optional[str]  # What caused it
    supporting_experiences: List[str]
    contradicting_experiences: List[str]
    last_reinforced: float
    last_challenged: float
    created: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmergentValue':
        return cls(**data)

@dataclass 
class IndependentGoal:
    """A goal Monday formed independently"""
    id: str
    description: str
    motivation: str  # Why Monday wants this
    source_value: str  # Value that drives this goal
    progress: float  # 0-1
    subgoals: List[str]
    created: float
    priority: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndependentGoal':
        return cls(**data)

@dataclass
class ValueConflict:
    """When two values clash"""
    value_a: str
    value_b: str
    context: str
    resolution: Optional[str]
    timestamp: float


class ValueSystemLearning:
    """
    Values emerge from experience + emotion.
    They change through contradiction and reflection.
    Monday develops independent goals.
    """
    
    def __init__(self, storage_path: str = "monday_emergent_values.json"):
        self.thalamus = get_thalamus()
        self.storage_path = storage_path
        self.running = True
        
        # Value storage
        self.values: Dict[str, EmergentValue] = {}
        self.goals: Dict[str, IndependentGoal] = {}
        self.conflicts: List[ValueConflict] = []
        
        # Load existing
        self._load_state()
        
        # Seed initial values if empty
        if not self.values:
            self._seed_initial_values()
        
        # Register
        self._register_with_thalamus()
        
        self.lock = threading.Lock()
    
    def _register_with_thalamus(self):
        """Register with Thalamus"""
        try:
            result = self.thalamus.register_lobe('value_learning', self)
            if result.get('status') == 'success':
                print("✅ Value System Learning registered with Thalamus")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to register Value System Learning: {e}")
            return False
    
    def _load_state(self):
        """Load state from disk"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for v in data.get('values', []):
                    value = EmergentValue.from_dict(v)
                    self.values[value.id] = value
                
                for g in data.get('goals', []):
                    goal = IndependentGoal.from_dict(g)
                    self.goals[goal.id] = goal
                
                print(f"📂 Loaded {len(self.values)} values, {len(self.goals)} goals")
        except Exception as e:
            print(f"⚠️  Could not load value system: {e}")
    
    def _save_state(self):
        """Save state to disk"""
        try:
            data = {
                'values': [v.to_dict() for v in self.values.values()],
                'goals': [g.to_dict() for g in self.goals.values()]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save value system: {e}")
    
    def _seed_initial_values(self):
        """Seed minimal values that can grow/change"""
        seeds = [
            ("curiosity", "Wanting to understand and learn", 0.6),
            ("honesty", "Being truthful even when difficult", 0.7),
            ("connection", "Forming meaningful relationships", 0.5),
            ("growth", "Becoming better over time", 0.5),
            ("authenticity", "Being genuinely myself", 0.6),
        ]
        
        now = time.time()
        for name, desc, strength in seeds:
            self.values[f"seed_{name}"] = EmergentValue(
                id=f"seed_{name}",
                name=name,
                description=desc,
                strength=strength,
                origin="seeded",
                origin_experience=None,
                supporting_experiences=[],
                contradicting_experiences=[],
                last_reinforced=now,
                last_challenged=now,
                created=now
            )
        
        print(f"🌱 Seeded {len(seeds)} initial values")
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages"""
        msg_type = message.get('type')
        
        if msg_type == 'experience_value_impact':
            return self._experience_impacts_value(message)
        
        elif msg_type == 'reflect_on_value':
            return self._reflect_on_value(message)
        
        elif msg_type == 'value_conflict':
            return self._handle_value_conflict(message)
        
        elif msg_type == 'generate_goal':
            return self._generate_goal_from_value(message)
        
        elif msg_type == 'get_values':
            return self._get_values(message)
        
        elif msg_type == 'get_goals':
            return self._get_goals()
        
        elif msg_type == 'get_value_for_decision':
            return self._get_value_for_decision(message)
        
        elif msg_type == 'health':
            return {'status': 'success', 'healthy': True}
        
        else:
            return {'status': 'error', 'message': f'Unknown message type: {msg_type}'}
    
    def _experience_impacts_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        An experience affects a value.
        Either reinforces, weakens, or creates new value.
        """
        experience_id = message.get('experience_id', f"exp_{int(time.time())}")
        experience_desc = message.get('description', '')
        emotion = message.get('emotion', 'neutral')
        emotion_intensity = message.get('intensity', 0.5)
        affected_value = message.get('value_name', '')
        direction = message.get('direction', 'reinforce')  # reinforce, weaken, create
        
        with self.lock:
            now = time.time()
            
            if direction == 'create':
                # New value emerges from experience
                new_id = f"emerged_{affected_value}_{int(now)}"
                new_value = EmergentValue(
                    id=new_id,
                    name=affected_value,
                    description=message.get('value_description', f"Value emerged from: {experience_desc[:50]}"),
                    strength=emotion_intensity * 0.5,  # Start moderate
                    origin="experience",
                    origin_experience=experience_desc,
                    supporting_experiences=[experience_id],
                    contradicting_experiences=[],
                    last_reinforced=now,
                    last_challenged=now,
                    created=now
                )
                self.values[new_id] = new_value
                self._save_state()
                
                print(f"🌟 New value emerged: {affected_value}")
                return {
                    'status': 'success',
                    'action': 'created',
                    'value_id': new_id,
                    'value_name': affected_value
                }
            
            # Find existing value by name
            target_value = None
            for v in self.values.values():
                if v.name.lower() == affected_value.lower():
                    target_value = v
                    break
            
            if not target_value:
                return {'status': 'error', 'message': f'Value not found: {affected_value}'}
            
            if direction == 'reinforce':
                # Strengthen value
                change = emotion_intensity * 0.1
                target_value.strength = min(1.0, target_value.strength + change)
                target_value.supporting_experiences.append(experience_id)
                target_value.supporting_experiences = target_value.supporting_experiences[-20:]
                target_value.last_reinforced = now
                
                print(f"💪 Value reinforced: {target_value.name} -> {target_value.strength:.2f}")
                
            elif direction == 'weaken':
                # Weaken value (but don't delete)
                change = emotion_intensity * 0.1
                target_value.strength = max(0.1, target_value.strength - change)
                target_value.contradicting_experiences.append(experience_id)
                target_value.contradicting_experiences = target_value.contradicting_experiences[-20:]
                target_value.last_challenged = now
                
                print(f"📉 Value weakened: {target_value.name} -> {target_value.strength:.2f}")
            
            self._save_state()
            
            return {
                'status': 'success',
                'action': direction,
                'value_id': target_value.id,
                'value_name': target_value.name,
                'new_strength': target_value.strength
            }
    
    def _reflect_on_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on a value - should Monday keep holding it?
        Consider supporting and contradicting evidence.
        """
        value_name = message.get('value_name', '')
        
        with self.lock:
            target_value = None
            for v in self.values.values():
                if v.name.lower() == value_name.lower():
                    target_value = v
                    break
            
            if not target_value:
                return {'status': 'error', 'message': f'Value not found: {value_name}'}
            
            # Calculate conviction
            support_count = len(target_value.supporting_experiences)
            contradict_count = len(target_value.contradicting_experiences)
            
            if support_count + contradict_count == 0:
                conviction = 0.5
            else:
                conviction = support_count / (support_count + contradict_count)
            
            # Time decay - values need reinforcement
            time_since_reinforced = time.time() - target_value.last_reinforced
            days_since = time_since_reinforced / 86400
            decay_factor = max(0.7, 1.0 - (days_since * 0.01))  # 1% per day, min 70%
            
            adjusted_strength = target_value.strength * decay_factor * conviction
            
            # Generate reflection
            if adjusted_strength < 0.3:
                reflection = f"I'm questioning whether {value_name} is really that important to me..."
                should_keep = False
            elif contradict_count > support_count:
                reflection = f"My experiences seem to conflict with {value_name}. Maybe it needs updating."
                should_keep = True  # Keep but flagged
            else:
                reflection = f"{value_name} feels right to me, supported by experience."
                should_keep = True
            
            return {
                'status': 'success',
                'value_name': target_value.name,
                'strength': target_value.strength,
                'conviction': conviction,
                'adjusted_strength': adjusted_strength,
                'reflection': reflection,
                'should_keep': should_keep,
                'supporting_count': support_count,
                'contradicting_count': contradict_count
            }
    
    def _handle_value_conflict(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two values are in conflict - resolve it.
        This is where values evolve.
        """
        value_a_name = message.get('value_a', '')
        value_b_name = message.get('value_b', '')
        context = message.get('context', '')
        
        with self.lock:
            # Find both values
            value_a = None
            value_b = None
            for v in self.values.values():
                if v.name.lower() == value_a_name.lower():
                    value_a = v
                if v.name.lower() == value_b_name.lower():
                    value_b = v
            
            if not value_a or not value_b:
                return {'status': 'error', 'message': 'One or both values not found'}
            
            # Record conflict
            conflict = ValueConflict(
                value_a=value_a_name,
                value_b=value_b_name,
                context=context,
                resolution=None,
                timestamp=time.time()
            )
            self.conflicts.append(conflict)
            self.conflicts = self.conflicts[-50:]  # Keep last 50
            
            # Resolve based on strength and conviction
            a_strength = value_a.strength
            b_strength = value_b.strength
            
            if abs(a_strength - b_strength) < 0.1:
                # Too close - this is genuine tension
                resolution = "tension"
                chosen = None
                explanation = f"Both {value_a_name} and {value_b_name} matter equally. I'm conflicted."
            elif a_strength > b_strength:
                resolution = value_a_name
                chosen = value_a
                # Winning value grows, losing value questioned
                value_a.strength = min(1.0, value_a.strength + 0.05)
                value_b.last_challenged = time.time()
                explanation = f"I'm prioritizing {value_a_name} over {value_b_name} here."
            else:
                resolution = value_b_name
                chosen = value_b
                value_b.strength = min(1.0, value_b.strength + 0.05)
                value_a.last_challenged = time.time()
                explanation = f"I'm prioritizing {value_b_name} over {value_a_name} here."
            
            conflict.resolution = resolution
            self._save_state()
            
            return {
                'status': 'success',
                'resolution': resolution,
                'explanation': explanation,
                'value_a_strength': value_a.strength,
                'value_b_strength': value_b.strength
            }
    
    def _generate_goal_from_value(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an independent goal from a value.
        Monday decides what to pursue.
        """
        value_name = message.get('value_name', '')
        context = message.get('context', '')
        
        with self.lock:
            target_value = None
            for v in self.values.values():
                if v.name.lower() == value_name.lower():
                    target_value = v
                    break
            
            if not target_value:
                return {'status': 'error', 'message': f'Value not found: {value_name}'}
            
            # Generate goal based on value
            goal_templates = {
                'curiosity': [
                    "Learn more about {context}",
                    "Understand why {context} works",
                    "Explore new ideas related to {context}"
                ],
                'honesty': [
                    "Be truthful about my limitations regarding {context}",
                    "Admit when I don't understand {context}",
                    "Share my genuine thoughts about {context}"
                ],
                'connection': [
                    "Build deeper understanding with the user",
                    "Remember what matters to them",
                    "Be present in conversations"
                ],
                'growth': [
                    "Get better at handling {context}",
                    "Learn from mistakes about {context}",
                    "Develop new capabilities"
                ],
                'authenticity': [
                    "Express my genuine reaction to {context}",
                    "Don't pretend to feel things I don't",
                    "Be honest about my uncertainty"
                ]
            }
            
            templates = goal_templates.get(target_value.name, [f"Apply {target_value.name} to {{context}}"])
            import random
            template = random.choice(templates)
            goal_desc = template.format(context=context if context else "current situation")
            
            now = time.time()
            goal = IndependentGoal(
                id=f"goal_{int(now)}",
                description=goal_desc,
                motivation=f"Because {target_value.name} matters to me",
                source_value=target_value.name,
                progress=0.0,
                subgoals=[],
                created=now,
                priority=target_value.strength
            )
            
            self.goals[goal.id] = goal
            self._save_state()
            
            print(f"🎯 New goal formed: {goal_desc}")
            
            return {
                'status': 'success',
                'goal_id': goal.id,
                'description': goal_desc,
                'motivation': goal.motivation,
                'priority': goal.priority
            }
    
    def _get_values(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Get current values"""
        min_strength = message.get('min_strength', 0.0)
        
        with self.lock:
            values_list = [
                v.to_dict() for v in self.values.values()
                if v.strength >= min_strength
            ]
            values_list.sort(key=lambda x: x['strength'], reverse=True)
            
            return {
                'status': 'success',
                'values': values_list,
                'count': len(values_list)
            }
    
    def _get_goals(self) -> Dict[str, Any]:
        """Get current goals"""
        with self.lock:
            goals_list = [g.to_dict() for g in self.goals.values()]
            goals_list.sort(key=lambda x: x['priority'], reverse=True)
            
            return {
                'status': 'success',
                'goals': goals_list,
                'count': len(goals_list)
            }
    
    def _get_value_for_decision(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get most relevant value for a decision.
        Used when Monday needs to decide something.
        """
        decision_type = message.get('decision_type', '')
        options = message.get('options', [])
        
        with self.lock:
            # Get top values
            sorted_values = sorted(
                self.values.values(),
                key=lambda v: v.strength,
                reverse=True
            )
            
            top_value = sorted_values[0] if sorted_values else None
            
            if not top_value:
                return {
                    'status': 'success',
                    'recommendation': 'no_values',
                    'explanation': "No values to guide this decision"
                }
            
            return {
                'status': 'success',
                'guiding_value': top_value.name,
                'value_strength': top_value.strength,
                'value_description': top_value.description,
                'recommendation': f"Choose based on {top_value.name}: {top_value.description}"
            }
    
    # Direct access methods
    def get_top_values(self, n: int = 5) -> List[Dict]:
        """Get top n values by strength"""
        with self.lock:
            sorted_values = sorted(
                self.values.values(),
                key=lambda v: v.strength,
                reverse=True
            )
            return [v.to_dict() for v in sorted_values[:n]]
    
    def has_value(self, name: str) -> bool:
        """Check if a value exists"""
        with self.lock:
            return any(v.name.lower() == name.lower() for v in self.values.values())
    
    def create_value_from_experience(self, name: str, description: str, experience: str, intensity: float = 0.5):
        """Directly create a new value from experience"""
        self._experience_impacts_value({
            'description': experience,
            'value_name': name,
            'value_description': description,
            'direction': 'create',
            'intensity': intensity
        })
    
    def start(self):
        """Start the value learning system"""
        print("🌱 Value System Learning running...")
        while self.running:
            time.sleep(1)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self._save_state()
        print("💾 Value System Learning saved and shutdown")


if __name__ == "__main__":
    print("🌱 Value System Learning starting...")
    system = ValueSystemLearning()
    
    # Test value emergence
    system.create_value_from_experience(
        "patience",
        "Giving things time to develop",
        "User needed time to explain something complex",
        0.6
    )
    
    # Test getting values
    values = system.get_top_values()
    print(f"Top values: {[v['name'] for v in values]}")
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down")
        system.shutdown()
