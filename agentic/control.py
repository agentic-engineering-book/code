"""Resource budgets that are checked before an action runs (Chapter 27)."""
from dataclasses import dataclass


@dataclass
class Budget:
    """Hard step and cost limits for one task.

    The controller asks ``refusal(cost)`` before acting and calls
    ``charge(cost)`` only for actions that were allowed, so a limit is
    never discovered after it has already been crossed.
    """

    max_steps: int = 10
    max_cost: float = 1.0
    steps_used: int = 0
    cost_used: float = 0.0

    def refusal(self, cost):
        """Return the reason the next action may not run, or None."""
        if self.steps_used >= self.max_steps:
            return "step_budget"
        if self.cost_used + cost > self.max_cost + 1e-9:
            return "cost_budget"
        return None

    def charge(self, cost):
        reason = self.refusal(cost)
        if reason:
            raise RuntimeError(f"budget exceeded: {reason}")
        self.steps_used += 1
        self.cost_used = round(self.cost_used + cost, 6)

    @property
    def cost_remaining(self):
        return round(self.max_cost - self.cost_used, 6)
