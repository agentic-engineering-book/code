"""The minimal reusable agent loop developed in Chapter 3."""
from agentic.tools import TOOLS, execute


class Agent:
    def __init__(self, model, tools=TOOLS, max_steps=10):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def run(self, goal):
        messages = [{"role": "user", "content": goal}]

        for step in range(self.max_steps):
            decision = self.model.generate(messages)
            messages.append({"role": "assistant", "content": decision})

            if decision.get("done"):
                return decision["answer"]

            observation = execute(decision, tools=self.tools)
            messages.append({"role": "tool", "content": str(observation)})

        raise RuntimeError("Step limit reached")
