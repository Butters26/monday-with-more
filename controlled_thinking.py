"""
Monday's Controlled Thinking System
Handles deliberate, focused reasoning with goal-directed attention and synthesis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class ReasoningGoal:
    """Represents a specific reasoning goal or objective."""
    description: str
    priority: int = 1  # 1-10, higher is more important
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed: bool = False
    conclusion: Optional[str] = None


class ControlledThinking:
    """
    Handles Monday's deliberate, focused reasoning system.
    
    This class manages goal-directed thinking, reasoning steps,
    attention shifting, and conclusion synthesis.
    """
    
    def __init__(self, max_reasoning_depth: int = 10):
        """
        Initialize the Controlled Thinking system.
        
        Args:
            max_reasoning_depth: Maximum number of reasoning steps allowed
        """
        self.max_reasoning_depth = max_reasoning_depth
        self.current_goal: Optional[ReasoningGoal] = None
        self.reasoning_chain: List[Dict[str, Any]] = []
        self.attention_focus: Optional[str] = None
        self.conclusions: List[str] = []
        
    def start_reasoning(self, goal_description: str, priority: int = 5, 
                       context: Optional[Dict[str, Any]] = None) -> ReasoningGoal:
        """
        Start a new reasoning process with a specific goal.
        
        Args:
            goal_description: What we're trying to reason about
            priority: Priority level (1-10)
            context: Additional context information
            
        Returns:
            The created ReasoningGoal
        """
        if context is None:
            context = {}
            
        self.current_goal = ReasoningGoal(
            description=goal_description,
            priority=priority,
            context=context
        )
        
        self.reasoning_chain = []
        self.attention_focus = goal_description
        self.conclusions = []
        
        # Log the start of reasoning
        self._add_reasoning_step(
            step_type="initialization",
            content=f"Starting reasoning about: {goal_description}",
            metadata={"priority": priority}
        )
        
        return self.current_goal
    
    def take_reasoning_step(self, thought: str, step_type: str = "analysis",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Take a single step in the reasoning process.
        
        Args:
            thought: The reasoning thought or observation
            step_type: Type of reasoning step (analysis, hypothesis, evaluation, etc.)
            metadata: Additional metadata about this step
            
        Returns:
            The reasoning step that was added
        """
        if not self.current_goal:
            raise ValueError("No active reasoning goal. Call start_reasoning() first.")
        
        if len(self.reasoning_chain) >= self.max_reasoning_depth:
            raise ValueError(f"Maximum reasoning depth ({self.max_reasoning_depth}) reached.")
        
        step = self._add_reasoning_step(step_type, thought, metadata)
        
        # Auto-adjust attention based on step type
        if step_type in ["critical_insight", "hypothesis", "contradiction"]:
            self.attention_focus = thought[:100]  # Focus on first 100 chars
        
        return step
    
    def shift_attention(self, new_focus: str, reason: Optional[str] = None) -> None:
        """
        Deliberately shift attention to a new aspect of the problem.
        
        Args:
            new_focus: What to focus attention on
            reason: Why we're shifting attention
        """
        old_focus = self.attention_focus
        self.attention_focus = new_focus
        
        metadata = {
            "old_focus": old_focus,
            "new_focus": new_focus,
            "reason": reason
        }
        
        self._add_reasoning_step(
            step_type="attention_shift",
            content=f"Shifting attention to: {new_focus}",
            metadata=metadata
        )
    
    def evaluate_hypothesis(self, hypothesis: str, 
                          evidence_for: List[str],
                          evidence_against: List[str]) -> Dict[str, Any]:
        """
        Evaluate a hypothesis against evidence.
        
        Args:
            hypothesis: The hypothesis to evaluate
            evidence_for: Evidence supporting the hypothesis
            evidence_against: Evidence contradicting the hypothesis
            
        Returns:
            Evaluation results
        """
        evaluation = {
            "hypothesis": hypothesis,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "for_count": len(evidence_for),
            "against_count": len(evidence_against),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine strength of hypothesis
        if len(evidence_for) > len(evidence_against) * 2:
            evaluation["strength"] = "strong"
        elif len(evidence_for) > len(evidence_against):
            evaluation["strength"] = "moderate"
        elif len(evidence_for) == len(evidence_against):
            evaluation["strength"] = "uncertain"
        else:
            evaluation["strength"] = "weak"
        
        self._add_reasoning_step(
            step_type="hypothesis_evaluation",
            content=f"Evaluating: {hypothesis}",
            metadata=evaluation
        )
        
        return evaluation
    
    def synthesize_conclusion(self, force: bool = False) -> str:
        """
        Synthesize a conclusion from the reasoning chain.
        
        Args:
            force: Force synthesis even if reasoning seems incomplete
            
        Returns:
            The synthesized conclusion
        """
        if not self.current_goal:
            raise ValueError("No active reasoning goal.")
        
        if len(self.reasoning_chain) < 2 and not force:
            raise ValueError("Insufficient reasoning steps to synthesize conclusion.")
        
        # Gather key insights from reasoning chain
        key_insights = [
            step["content"] for step in self.reasoning_chain
            if step["type"] in ["critical_insight", "hypothesis_evaluation", "analysis"]
        ]
        
        # Create conclusion summary
        conclusion = self._generate_conclusion_summary(key_insights)
        
        self.conclusions.append(conclusion)
        self.current_goal.conclusion = conclusion
        self.current_goal.completed = True
        
        self._add_reasoning_step(
            step_type="conclusion",
            content=conclusion,
            metadata={"total_steps": len(self.reasoning_chain)}
        )
        
        return conclusion
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current reasoning process.
        
        Returns:
            Summary dictionary with key information
        """
        return {
            "goal": self.current_goal.description if self.current_goal else None,
            "completed": self.current_goal.completed if self.current_goal else False,
            "steps_taken": len(self.reasoning_chain),
            "current_focus": self.attention_focus,
            "conclusions": self.conclusions,
            "reasoning_chain": self.reasoning_chain
        }
    
    def reset(self) -> None:
        """Reset the reasoning system to initial state."""
        self.current_goal = None
        self.reasoning_chain = []
        self.attention_focus = None
        self.conclusions = []
    
    def _add_reasoning_step(self, step_type: str, content: str,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to add a reasoning step to the chain.
        
        Args:
            step_type: Type of reasoning step
            content: Content of the step
            metadata: Additional metadata
            
        Returns:
            The created step
        """
        if metadata is None:
            metadata = {}
        
        step = {
            "type": step_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "step_number": len(self.reasoning_chain) + 1,
            "metadata": metadata
        }
        
        self.reasoning_chain.append(step)
        return step
    
    def _generate_conclusion_summary(self, key_insights: List[str]) -> str:
        """
        Generate a conclusion summary from key insights.
        
        Args:
            key_insights: List of key insights from reasoning
            
        Returns:
            Synthesized conclusion
        """
        if not key_insights:
            return f"Completed reasoning about: {self.current_goal.description}"
        
        conclusion_parts = [
            f"After {len(self.reasoning_chain)} reasoning steps about '{self.current_goal.description}':",
        ]
        
        # Add key insights
        for i, insight in enumerate(key_insights[:5], 1):  # Limit to top 5
            conclusion_parts.append(f"{i}. {insight[:200]}")  # Limit length
        
        return "\n".join(conclusion_parts)
    
    def export_reasoning_chain(self, filepath: Optional[str] = None) -> str:
        """
        Export the reasoning chain to JSON format.
        
        Args:
            filepath: Optional file path to save to
            
        Returns:
            JSON string of reasoning chain
        """
        export_data = {
            "goal": {
                "description": self.current_goal.description,
                "priority": self.current_goal.priority,
                "completed": self.current_goal.completed,
                "conclusion": self.current_goal.conclusion
            } if self.current_goal else None,
            "reasoning_chain": self.reasoning_chain,
            "conclusions": self.conclusions,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        json_str = json.dumps(export_data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str


def test_controlled_thinking():
    """Test function demonstrating the ControlledThinking system."""
    print("=" * 60)
    print("Testing Monday's Controlled Thinking System")
    print("=" * 60)
    
    # Initialize the system
    ct = ControlledThinking(max_reasoning_depth=15)
    
    # Start reasoning about a problem
    print("\n1. Starting reasoning process...")
    goal = ct.start_reasoning(
        goal_description="Determine the best approach for implementing user authentication",
        priority=8,
        context={"project": "web_app", "security_level": "high"}
    )
    print(f"   Goal: {goal.description}")
    print(f"   Priority: {goal.priority}")
    
    # Take reasoning steps
    print("\n2. Taking reasoning steps...")
    ct.take_reasoning_step(
        "User authentication requires balancing security and usability",
        step_type="analysis"
    )
    
    ct.take_reasoning_step(
        "Options include: JWT tokens, session cookies, OAuth2",
        step_type="hypothesis"
    )
    
    # Shift attention
    print("\n3. Shifting attention...")
    ct.shift_attention(
        "Security implications of each approach",
        reason="Need to prioritize security given high security level requirement"
    )
    
    ct.take_reasoning_step(
        "JWT tokens are stateless but require careful key management",
        step_type="analysis"
    )
    
    ct.take_reasoning_step(
        "Session cookies are simpler but require server-side state",
        step_type="analysis"
    )
    
    # Evaluate a hypothesis
    print("\n4. Evaluating hypothesis...")
    evaluation = ct.evaluate_hypothesis(
        hypothesis="JWT tokens are the best choice for this application",
        evidence_for=[
            "Stateless nature scales better",
            "Works well with microservices",
            "Industry standard for APIs"
        ],
        evidence_against=[
            "More complex to implement securely",
            "Token revocation is challenging"
        ]
    )
    print(f"   Hypothesis strength: {evaluation['strength']}")
    
    # Take more reasoning steps
    ct.take_reasoning_step(
        "Given the high security requirement and API-first architecture, JWT with proper key rotation is optimal",
        step_type="critical_insight"
    )
    
    # Synthesize conclusion
    print("\n5. Synthesizing conclusion...")
    conclusion = ct.synthesize_conclusion()
    print(f"   Conclusion:\n{conclusion}")
    
    # Get summary
    print("\n6. Reasoning summary...")
    summary = ct.get_reasoning_summary()
    print(f"   Total steps: {summary['steps_taken']}")
    print(f"   Completed: {summary['completed']}")
    print(f"   Final focus: {summary['current_focus']}")
    
    # Export reasoning chain
    print("\n7. Exporting reasoning chain...")
    json_export = ct.export_reasoning_chain()
    print(f"   Exported {len(json_export)} characters of reasoning data")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_controlled_thinking()
