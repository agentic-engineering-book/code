"""Experiment 31 (Chapter 17): Agent as tool."""
import json
import textwrap

from agentic import Agent, calculator
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel, schema

GOAL = "Find the reported value of X, then calculate X * 1.10."
SEARCH = schema("search", "Search the company reports.", query="search terms")
RESEARCHER = schema("researcher", "A research agent that finds facts in "
                    "the company reports.", question="the question to research")


def found(query):
    return "Q3 report: the reported value of X is 80."


def nothing(query):
    return "no result"


def make_chain():
    """Every report points to the next one; none contains the value."""
    reports = iter(range(2, 100))

    def chain(query):
        n = next(reports)
        return (f"Report R{n - 1}: X is not given here; its value is "
                f"reported in report R{n}.")
    return chain


class ResearchAgent:
    """A child agent with its own model, tool, and step budget."""

    def __init__(self, sources):
        self.sources, self.searches, self.model_calls = sources, 0, 0

    def search(self, query):
        self.searches += 1
        return self.sources(query)

    def run(self, question, max_steps=5):
        model = OpenAIModel(tools=[SEARCH], system="You are a research "
                            "agent. Use search to answer the question. "
                            "Reply with the answer only.")
        child = Agent(model, tools={"search": self.search},
                      max_steps=max_steps)
        try:
            answer, status = child.run(question), "complete"
        except RuntimeError:  # the delegated step limit
            answer, status = None, "incomplete"
        self.model_calls += len(model.calls)
        return json.dumps({"status": status, "answer": answer,
                           "steps_used": len(model.calls)})


def run_parent(label, sources):
    print(label)
    specialist, actions = ResearchAgent(sources), []

    def researcher(question):
        actions.append("researcher")
        result = specialist.run(question)
        print("  researcher returned:", textwrap.shorten(result, 54))
        return result

    def calculate(expression):
        actions.append("calculator")
        return calculator(expression)

    parent = Agent(OpenAIModel(tools=[RESEARCHER, CALCULATOR_SCHEMA]),
                   tools={"researcher": researcher, "calculator": calculate},
                   max_steps=6)
    answer = parent.run(GOAL)
    print(f"  parent actions: {actions}")
    print(f"  hidden child work: model calls={specialist.model_calls}, "
          f"searches={specialist.searches}")
    print("  answer:", textwrap.shorten(answer, 68))


run_parent("source has the value", found)
run_parent("source has nothing", nothing)
run_parent("each report points to the next", make_chain())
