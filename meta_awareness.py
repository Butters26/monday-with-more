#!/usr/bin/env python3
"""
Meta-Awareness - Monday's awareness of her own thinking
She can notice spontaneous thoughts, choose to engage or dismiss them,
and shift between focused and wandering modes
"""

import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ThinkingMode(Enum):
    """Different modes of thinking"""
    WANDERING = "wandering"      # Let spontaneous thoughts flow
    FOCUSED = "focused"          # Pursuing controlled reasoning
    TRANSITIONING = "transitioning"  # Shifting between modes


@dataclass
class MetaState:
    """Current meta-cognitive state"""
    mode: ThinkingMode = ThinkingMode.WANDERING
    awareness_level: float = 0.7  # How aware of own thinking (0-1)
    engagement_threshold: float = 0.6  # How interesting must thought be to engage
    distraction_resistance: float = 0.5  # How much she resists spontaneous thoughts while focused
    
    # Tracking
    spontaneous_thoughts_noticed: int = 0
    spontaneous_thoughts_engaged: int = 0
    spontaneous_thoughts_dismissed: int = 0
    mode_shifts: int = 0


class MetaAwareness:
    """
    Meta-layer that manages both spontaneous and controlled thinking
    She's AWARE of both streams and can choose how to engage
    """
    
    def __init__(self):
        self.state = MetaState()
        
        # References to thought systems (will be set externally)
        self.spontaneous_system = None
        self.controlled_system = None
        
        # Current thoughts
        self.current_spontaneous_thought = None
        self.noticed_thoughts = []  # Thoughts she's noticed but not engaged
        
    def set_spontaneous_system(self, system):
        """Connect to spontaneous thought generator"""
        self.spontaneous_system = system
    
    def set_controlled_system(self, system):
        """Connect to controlled thinking system"""
        self.controlled_system = system
    
    def notice_spontaneous_thought(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """
        A spontaneous thought occurred - does she notice it?
        
        Args:
            thought: The spontaneous thought that occurred
            
        Returns:
            Meta-response: what she does with the thought
        """
        self.current_spontaneous_thought = thought
        self.state.spontaneous_thoughts_noticed += 1
        
        # Does she notice it? (awareness level determines this)
        import random
        if random.random() > self.state.awareness_level:
            # Thought passes by unnoticed
            return {
                "action": "unnoticed",
                "thought": thought["text"],
                "meta_comment": None
            }
        
        # She noticed it
        self.noticed_thoughts.append(thought)
        
        # Meta-comment about noticing
        meta_comment = self._generate_meta_comment(thought)
        
        # Should she engage with it?
        should_engage = self._should_engage_with_thought(thought)
        
        if should_engage:
            response = self._engage_with_thought(thought)
            response["meta_comment"] = meta_comment
            return response
        else:
            self.state.spontaneous_thoughts_dismissed += 1
            return {
                "action": "dismissed",
                "thought": thought["text"],
                "meta_comment": meta_comment,
                "reason": "Not interesting enough right now"
            }
    
    def _generate_meta_comment(self, thought: Dict[str, Any]) -> str:
        """Generate self-aware comment about the thought"""
        trigger = thought.get("trigger", "unknown")
        
        comments = {
            "memory": [
                "Huh, that memory just popped up",
                "Why am I remembering this now?",
                "That thought came out of nowhere"
            ],
            "association": [
                "My mind is making connections",
                "One thought led to another",
                "I see how these relate"
            ],
            "curiosity": [
                "I'm curious about something",
                "That's an interesting question",
                "I want to know more about this"
            ],
            "rumination": [
                "I keep coming back to this",
                "Can't stop thinking about this",
                "Why am I dwelling on this?"
            ],
            "creative": [
                "I'm imagining something",
                "What if this scenario happened?",
                "Creating a mental picture"
            ],
            "self_aware": [
                "Thinking about my own thinking",
                "Meta-moment happening",
                "Why am I even thinking this?"
            ],
        }
        
        import random
        if trigger in comments:
            return random.choice(comments[trigger])
        return "I just had a thought"
    
    def _should_engage_with_thought(self, thought: Dict[str, Any]) -> bool:
        """Decide whether to engage with spontaneous thought"""
        # If already focused, resist spontaneous thoughts
        if self.state.mode == ThinkingMode.FOCUSED:
            import random
            if random.random() < self.state.distraction_resistance:
                return False
        
        # Calculate thought "interestingness"
        trigger = thought.get("trigger", "random")
        
        # Different triggers have different base interest levels
        interest_weights = {
            "curiosity": 0.8,
            "creative": 0.7,
            "self_aware": 0.7,
            "memory": 0.6,
            "association": 0.5,
            "rumination": 0.5,
            "emotion": 0.6,
            "random": 0.3,
        }
        
        base_interest = interest_weights.get(trigger, 0.5)
        
        # Engage if interest exceeds threshold
        return base_interest >= self.state.engagement_threshold
    
    def _engage_with_thought(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Engage with the spontaneous thought - make it controlled"""
        self.state.spontaneous_thoughts_engaged += 1
        
        # Shift to focused mode if not already
        if self.state.mode != ThinkingMode.FOCUSED:
            self.shift_to_focused(reason=f"Engaging with thought: {thought['text'][:50]}")
        
        # Extract topic from thought
        concepts = thought.get("concepts", [])
        topic = concepts[0] if concepts else thought["text"][:30]
        
        # Start controlled reasoning about it
        if self.controlled_system:
            question = self._generate_question_from_thought(thought)
            # This would trigger controlled reasoning
            return {
                "action": "engaged",
                "thought": thought["text"],
                "topic": topic,
                "question": question,
                "shifted_to_focused": True
            }
        
        return {
            "action": "engaged",
            "thought": thought["text"],
            "topic": topic,
        }
    
    def _generate_question_from_thought(self, thought: Dict[str, Any]) -> str:
        """Turn a spontaneous thought into a reasoning question"""
        text = thought["text"]
        trigger = thought.get("trigger", "unknown")
        
        if trigger == "curiosity":
            # Already a question probably
            if "?" in text:
                return text
            return f"I wonder: {text}"
        
        elif trigger == "creative":
            return f"What would happen if {text}?"
        
        elif trigger == "memory":
            return f"Why did I remember: {text}?"
        
        elif trigger == "rumination":
            return f"Why can't I stop thinking about: {text}?"
        
        else:
            return f"What do I actually think about: {text}?"
    
    def shift_to_focused(self, reason: Optional[str] = None):
        """Shift from wandering to focused mode"""
        if self.state.mode == ThinkingMode.FOCUSED:
            return  # Already focused
        
        old_mode = self.state.mode
        self.state.mode = ThinkingMode.FOCUSED
        self.state.mode_shifts += 1
        
        print(f"\n🔄 [META] Shifting to FOCUSED mode")
        if reason:
            print(f"   Reason: {reason}")
        print(f"   Increasing distraction resistance\n")
        
        # When focused, resist spontaneous thoughts more
        self.state.distraction_resistance = 0.8
    
    def shift_to_wandering(self, reason: Optional[str] = None):
        """Shift from focused to wandering mode"""
        if self.state.mode == ThinkingMode.WANDERING:
            return  # Already wandering
        
        old_mode = self.state.mode
        self.state.mode = ThinkingMode.WANDERING
        self.state.mode_shifts += 1
        
        print(f"\n🔄 [META] Shifting to WANDERING mode")
        if reason:
            print(f"   Reason: {reason}")
        print(f"   Letting thoughts flow freely\n")
        
        # When wandering, allow spontaneous thoughts
        self.state.distraction_resistance = 0.2
        self.state.engagement_threshold = 0.5
    
    def evaluate_current_mode(self) -> Dict[str, Any]:
        """Evaluate if current mode is appropriate"""
        # Should check: 
        # - If focused but no goal → shift to wandering
        # - If wandering but high curiosity about something → shift to focused
        # - If focused too long → shift to wandering for mental break
        
        evaluation = {
            "current_mode": self.state.mode.value,
            "should_shift": False,
            "reason": None,
        }
        
        if self.state.mode == ThinkingMode.FOCUSED:
            # Check if we still have a goal
            if self.controlled_system and not self.controlled_system.current_goal:
                evaluation["should_shift"] = True
                evaluation["reason"] = "No active reasoning goal"
                evaluation["suggested_mode"] = "wandering"
        
        elif self.state.mode == ThinkingMode.WANDERING:
            # Check if we've noticed several high-interest thoughts
            recent_noticed = self.noticed_thoughts[-5:] if len(self.noticed_thoughts) >= 5 else self.noticed_thoughts
            high_interest_count = sum(1 for t in recent_noticed if t.get("trigger") in ["curiosity", "creative", "self_aware"])
            
            if high_interest_count >= 3:
                evaluation["should_shift"] = True
                evaluation["reason"] = "Multiple interesting thoughts - should focus"
                evaluation["suggested_mode"] = "focused"
        
        return evaluation
    
    def adjust_awareness(self, delta: float):
        """Adjust awareness level"""
        self.state.awareness_level = max(0.0, min(1.0, self.state.awareness_level + delta))
    
    def adjust_engagement_threshold(self, delta: float):
        """Adjust how selective she is about engaging thoughts"""
        self.state.engagement_threshold = max(0.0, min(1.0, self.state.engagement_threshold + delta))
    
    def get_meta_state_summary(self) -> Dict[str, Any]:
        """Get summary of meta-cognitive state"""
        engagement_rate = 0.0
        if self.state.spontaneous_thoughts_noticed > 0:
            engagement_rate = self.state.spontaneous_thoughts_engaged / self.state.spontaneous_thoughts_noticed
        
        return {
            "mode": self.state.mode.value,
            "awareness_level": self.state.awareness_level,
            "engagement_threshold": self.state.engagement_threshold,
            "distraction_resistance": self.state.distraction_resistance,
            "thoughts_noticed": self.state.spontaneous_thoughts_noticed,
            "thoughts_engaged": self.state.spontaneous_thoughts_engaged,
            "thoughts_dismissed": self.state.spontaneous_thoughts_dismissed,
            "engagement_rate": engagement_rate,
            "mode_shifts": self.state.mode_shifts,
        }


def test_meta_awareness():
    """Test meta-awareness system"""
    print("=" * 60)
    print("META-AWARENESS TEST")
    print("=" * 60)
    
    meta = MetaAwareness()
    
    # Simulate spontaneous thoughts
    thoughts = [
        {"text": "I wonder why humans sleep", "trigger": "curiosity", "concepts": ["sleep", "humans"]},
        {"text": "coffee makes me think of tired", "trigger": "association", "concepts": ["coffee", "tired"]},
        {"text": "Random thought: consciousness", "trigger": "random", "concepts": ["consciousness"]},
        {"text": "What if I could see colors?", "trigger": "creative", "concepts": ["colors", "imagine"]},
        {"text": "Why am I thinking about this?", "trigger": "self_aware", "concepts": ["thinking"]},
        {"text": "I remember Matthew created me", "trigger": "memory", "concepts": ["matthew", "creation"]},
    ]
    
    print(f"\nInitial mode: {meta.state.mode.value}")
    print(f"Awareness level: {meta.state.awareness_level:.2f}")
    print(f"Engagement threshold: {meta.state.engagement_threshold:.2f}\n")
    
    # Process each thought
    for i, thought in enumerate(thoughts, 1):
        print(f"--- Spontaneous Thought {i} ---")
        print(f"[{thought['trigger'].upper()}] {thought['text']}")
        
        response = meta.notice_spontaneous_thought(thought)
        
        print(f"Action: {response['action']}")
        if response.get("meta_comment"):
            print(f"Meta: \"{response['meta_comment']}\"")
        if response.get("question"):
            print(f"Question generated: {response['question']}")
        print()
        
        time.sleep(0.5)
        
        # Check if should shift mode
        if i == 3:
            evaluation = meta.evaluate_current_mode()
            if evaluation["should_shift"]:
                print(f"[EVALUATION] Should shift: {evaluation['reason']}")
                if evaluation["suggested_mode"] == "focused":
                    meta.shift_to_focused(evaluation["reason"])
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    summary = meta.get_meta_state_summary()
    print(f"Final mode: {summary['mode']}")
    print(f"Thoughts noticed: {summary['thoughts_noticed']}")
    print(f"Thoughts engaged: {summary['thoughts_engaged']}")
    print(f"Thoughts dismissed: {summary['thoughts_dismissed']}")
    print(f"Engagement rate: {summary['engagement_rate']:.2%}")
    print(f"Mode shifts: {summary['mode_shifts']}")
    print("=" * 60)


if __name__ == "__main__":
    test_meta_awareness()
