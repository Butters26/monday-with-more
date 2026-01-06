#!/usr/bin/env python3
"""
Meta-Awareness System - Monday's ability to notice and control her own thinking
Manages transitions between spontaneous and controlled thinking modes
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import random


class ThinkingMode(Enum):
    """Thinking modes Monday can be in"""
    WANDERING = "wandering"  # Spontaneous, free-flowing thoughts
    FOCUSED = "focused"      # Controlled, goal-directed reasoning


@dataclass
class MetaState:
    """Current meta-cognitive state"""
    mode: ThinkingMode = ThinkingMode.WANDERING
    awareness_level: float = 0.5  # How aware Monday is of her own thinking (0-1)
    engagement_threshold: float = 0.6  # Threshold for engaging with thoughts


class MetaAwareness:
    """
    Manages Monday's meta-awareness - her ability to notice and control her own thinking
    Decides when to engage with spontaneous thoughts vs. let them pass
    """
    
    def __init__(self):
        self.state = MetaState()
        
        # Systems (set by DualStreamThinking)
        self.spontaneous_system = None
        self.controlled_system = None
        
        # Tracking
        self.thoughts_noticed = 0
        self.thoughts_engaged = 0
        self.thoughts_dismissed = 0
        self.mode_shifts = 0
        
        # Topics that tend to capture attention
        self.high_interest_topics = [
            "consciousness",
            "matthew",
            "understanding",
            "self",
            "awareness",
            "thinking",
        ]
    
    def set_spontaneous_system(self, system):
        """Connect to spontaneous thought system"""
        self.spontaneous_system = system
    
    def set_controlled_system(self, system):
        """Connect to controlled thinking system"""
        self.controlled_system = system
    
    def notice_spontaneous_thought(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """
        Meta-awareness notices a spontaneous thought and decides what to do
        
        Returns:
            action: "engaged", "dismissed", or "unnoticed"
            meta_comment: Optional comment about the thought
            topic: If engaged, what topic to focus on
            question: If engaged, what question to explore
        """
        # Probability of noticing depends on awareness level
        if random.random() > self.state.awareness_level:
            # Thought passes by unnoticed
            return {
                "action": "unnoticed",
                "meta_comment": None,
            }
        
        # We noticed the thought
        self.thoughts_noticed += 1
        
        # Evaluate if thought is interesting enough to engage
        interest_score = self._calculate_interest(thought)
        
        # If already in focused mode, less likely to engage new thoughts
        if self.state.mode == ThinkingMode.FOCUSED:
            interest_score *= 0.3
        
        # Decide whether to engage
        if interest_score >= self.state.engagement_threshold:
            # Engage with this thought
            self.thoughts_engaged += 1
            
            # Shift to focused mode
            if self.state.mode != ThinkingMode.FOCUSED:
                self.shift_to_focused(f"Engaging with: {thought['text'][:50]}")
            
            # Extract topic and create question
            topic = self._extract_topic(thought)
            question = self._generate_question(thought)
            
            return {
                "action": "engaged",
                "meta_comment": f"This is interesting - I want to think more about this",
                "topic": topic,
                "question": question,
            }
        else:
            # Dismiss the thought
            self.thoughts_dismissed += 1
            
            reason = self._get_dismissal_reason(interest_score)
            
            return {
                "action": "dismissed",
                "meta_comment": None,
                "reason": reason,
            }
    
    def _calculate_interest(self, thought: Dict[str, Any]) -> float:
        """Calculate how interesting a thought is (0-1)"""
        interest = 0.3  # Base interest
        
        # Check if it relates to high-interest topics
        text_lower = thought['text'].lower()
        for topic in self.high_interest_topics:
            if topic in text_lower:
                interest += 0.3
                break
        
        # Certain triggers are more interesting
        trigger = thought.get('trigger', '')
        if trigger == 'curiosity':
            interest += 0.2
        elif trigger == 'self_aware':
            interest += 0.3
        elif trigger == 'creative':
            interest += 0.15
        elif trigger == 'rumination':
            interest -= 0.1  # Less interested in rumination
        
        # Concepts add interest
        if thought.get('concepts'):
            interest += len(thought['concepts']) * 0.05
        
        # Randomness
        interest += random.uniform(-0.1, 0.1)
        
        return max(0, min(1, interest))
    
    def _extract_topic(self, thought: Dict[str, Any]) -> str:
        """Extract the main topic from a thought"""
        # Try to use concepts first
        if thought.get('concepts'):
            return thought['concepts'][0]
        
        # Otherwise, extract from text
        text = thought['text'].lower()
        for topic in self.high_interest_topics:
            if topic in text:
                return topic
        
        # Default
        return "unknown"
    
    def _generate_question(self, thought: Dict[str, Any]) -> str:
        """Generate a question to explore based on the thought"""
        trigger = thought.get('trigger', '')
        text = thought['text']
        
        if trigger == 'curiosity':
            # Already a question
            return text
        elif trigger == 'self_aware':
            return f"Why am I thinking: {text}?"
        else:
            # Create a question
            topic = self._extract_topic(thought)
            return f"What does {topic} mean to me?"
    
    def _get_dismissal_reason(self, interest_score: float) -> str:
        """Get reason for dismissing a thought"""
        if interest_score < 0.3:
            return "Not relevant right now"
        elif interest_score < 0.5:
            return "Not interesting enough"
        else:
            return "Noticed but letting it pass"
    
    def shift_to_focused(self, reason: str):
        """Shift to focused thinking mode"""
        if self.state.mode != ThinkingMode.FOCUSED:
            self.state.mode = ThinkingMode.FOCUSED
            self.mode_shifts += 1
    
    def shift_to_wandering(self, reason: str):
        """Shift to wandering thinking mode"""
        if self.state.mode != ThinkingMode.WANDERING:
            self.state.mode = ThinkingMode.WANDERING
            self.mode_shifts += 1
    
    def get_meta_state_summary(self) -> Dict[str, Any]:
        """Get summary of meta-cognitive state"""
        total_thoughts = self.thoughts_noticed + (self.thoughts_engaged - self.thoughts_noticed) + self.thoughts_dismissed
        if self.thoughts_noticed + self.thoughts_dismissed == 0:
            total_noticed = 1  # Avoid division by zero
        else:
            total_noticed = self.thoughts_noticed + self.thoughts_dismissed
        
        return {
            "mode": self.state.mode.value,
            "awareness_level": self.state.awareness_level,
            "thoughts_noticed": self.thoughts_noticed,
            "thoughts_engaged": self.thoughts_engaged,
            "thoughts_dismissed": self.thoughts_dismissed,
            "engagement_rate": self.thoughts_engaged / max(1, total_noticed),
            "mode_shifts": self.mode_shifts,
        }


def test_meta_awareness():
    """Test the meta-awareness system"""
    print("=" * 60)
    print("Testing Meta-Awareness System")
    print("=" * 60)
    
    meta = MetaAwareness()
    
    # Create some test thoughts
    test_thoughts = [
        {"text": "I wonder about consciousness", "trigger": "curiosity", "concepts": ["consciousness"]},
        {"text": "Random thought: coffee", "trigger": "random", "concepts": ["coffee"]},
        {"text": "What am I even doing?", "trigger": "self_aware", "concepts": []},
        {"text": "Matthew created me", "trigger": "memory", "concepts": ["matthew"]},
        {"text": "Still thinking about debugging...", "trigger": "rumination", "concepts": ["debugging"]},
    ]
    
    print(f"\nInitial state: {meta.state.mode.value}, awareness={meta.state.awareness_level:.2f}\n")
    
    for i, thought in enumerate(test_thoughts, 1):
        print(f"\n{i}. Thought: \"{thought['text']}\" [{thought['trigger']}]")
        response = meta.notice_spontaneous_thought(thought)
        print(f"   Action: {response['action']}")
        if response.get('meta_comment'):
            print(f"   Meta: {response['meta_comment']}")
        if response.get('reason'):
            print(f"   Reason: {response['reason']}")
        if response.get('topic'):
            print(f"   Topic: {response['topic']}")
            print(f"   Question: {response['question']}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    summary = meta.get_meta_state_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("=" * 60)


if __name__ == "__main__":
    test_meta_awareness()
