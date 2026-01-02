"""
ValueGoalManagementLobe: Value and goal management module for the AI brain architecture.
Handles value tracking, goal prioritization, and motivation signals.
"""

class ValueGoalManagementLobe:
    def __init__(self, thalamus=None):
        self.thalamus = thalamus
        self.values = {}
        self.goals = []

    def update_values(self, values):
        """Update value system based on input."""
        self.values.update(values)

    def add_goal(self, goal):
        """Add a new goal to the goal list."""
        self.goals.append(goal)

    def prioritize_goals(self):
        """Prioritize goals based on values and context."""
        # TODO: Implement prioritization logic
        # Simple prioritization: goals may be tuples (goal, priority) or strings
        def score(goal):
            if isinstance(goal, dict) and 'priority' in goal:
                return float(goal.get('priority', 0))
            if isinstance(goal, str):
                # score by matching value keywords
                s = 0.0
                for k, v in self.values.items():
                    if k in goal:
                        s += float(v)
                return s
            return 0.0

        self.goals.sort(key=score, reverse=True)
        return list(self.goals)

    def route_goals(self):
        """Route prioritized goals to relevant lobes via Thalamus."""
        if self.thalamus and self.goals:
            try:
                self.thalamus.send_message('executive_control', 'add_task', {'task': {'type': 'goal_batch', 'goals': self.goals}}, source='value_goal_management')
            except Exception as e:
                print(f"[ValueGoalManagementLobe] Error routing goals: {e}")

    def reset(self):
        self.values.clear()
        self.goals.clear()

    def process_message(self, message):
        msg_type = message.get('type')
        if 'content' in message:
            content = message.get('content', {})
        else:
            content = {k: v for k, v in message.items() if k not in ('type', '_message_id', 'message_id')}
        if msg_type == 'update_values':
            vals = content.get('values', {})
            self.update_values(vals)
            return {'status': 'success', 'values': self.values}
        elif msg_type == 'add_goal':
            goal = content.get('goal')
            if goal is None:
                return {'status': 'error', 'message': 'Missing goal'}
            self.add_goal(goal)
            return {'status': 'success', 'goals': list(self.goals)}
        elif msg_type == 'prioritize':
            prioritized = self.prioritize_goals()
            return {'status': 'success', 'prioritized_goals': prioritized}
        elif msg_type == 'route_goals':
            self.route_goals()
            return {'status': 'success', 'message': 'Goals routed'}
        elif msg_type == 'reset':
            self.reset()
            return {'status': 'success', 'message': 'ValueGoalManagementLobe reset'}
        else:
            return {'status': 'error', 'message': f'Unknown message type: {msg_type}'}

# TODO: Integrate with Thalamus and other lobes
# TODO: Add error handling, logging, and configuration
