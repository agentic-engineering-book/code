"""Experiment 27: Rule router as a LangGraph conditional edge."""
from framework_examples.support import branch

from agentic import calculator

TASKS = [("calculate 17 * 6", "math"), ("what is refund policy?", "policy"),
         ("write a short email", "write"), ("Calculate 3 + 4", "math")]
MISROUTE_COST = {"math": 1, "policy": 5, "write": 1}


def rule_router(state):
    task = state["value"]
    if task.startswith("calculate"):
        return "math"
    if "policy" in task:
        return "policy"
    return "write"


DESTINATIONS = {
    "math": lambda s: {"value": [
        "math", calculator(s["value"].removeprefix("calculate "))]},
    "policy": lambda s: {"value": ["policy", "retrieved policy text"]},
    "write": lambda s: {"value": ["write", "drafted text"]},
}


def run():
    routed, cost = [], 0
    for task, gold in TASKS:
        route, output = branch(DESTINATIONS, rule_router, task)
        routed.append([task, route, output])
        cost += 0 if route == gold else MISROUTE_COST[gold]
    return {"routed": routed, "misroute_cost": cost}


if __name__ == "__main__":
    print(run())
