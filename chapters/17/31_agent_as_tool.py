"""Experiment 31 (Chapter 17): Agent as tool."""
import json

from agentic import Agent, PolicyModel, ScriptedModel, calculator
from agentic import last_observation

SOURCES = {"X": "80"}
SEARCH = {"action": "search", "arguments": {"query": "X"}}


class ResearchAgent:
    """A child agent with its own model, tool, and step budget."""

    def __init__(self, model):
        self.model = model
        self.searches = 0

    def search(self, query):
        self.searches += 1
        return SOURCES.get(query, "no result")

    def run(self, question, max_steps):
        before = self.model.calls
        child = Agent(self.model, tools={"search": self.search},
                      max_steps=max_steps)
        try:
            answer, status = child.run(question), "complete"
        except RuntimeError:  # the child's step limit
            answer, status = None, "incomplete"
        return json.dumps({"status": status, "answer": answer,
                           "steps_used": self.model.calls - before})


def parent_policy(messages):
    observation = last_observation(messages)
    if observation is None:
        return {"action": "researcher",
                "arguments": {"question": "What is X?"}}
    if observation.startswith("{"):
        result = json.loads(observation)
        if result["status"] != "complete":
            return {"done": True, "answer": "escalate: research incomplete"}
        expression = f"{result['answer']} * 1.10"
        return {"action": "calculator",
                "arguments": {"expression": expression}}
    return {"done": True, "answer": f"X * 1.10 = {observation}"}


def run_parent(child_script, child_max_steps=5):
    specialist = ResearchAgent(ScriptedModel(child_script))
    actions = []

    def researcher(question):
        actions.append("researcher")
        result = specialist.run(question, max_steps=child_max_steps)
        print(f"  researcher returned: {result}")
        return result

    def calculate(expression):
        actions.append("calculator")
        return calculator(expression)

    parent = Agent(PolicyModel(parent_policy),
                   tools={"researcher": researcher, "calculator": calculate})
    answer = parent.run("Find X, then calculate X * 1.10.")
    print(f"  parent actions: {actions}")
    print(f"  hidden child searches: {specialist.searches}")
    print(f"  answer: {answer}")


print("cooperative specialist")
run_parent([SEARCH, {"done": True, "answer": "80"}])
print("looping specialist, delegated max_steps=5")
run_parent([SEARCH])
