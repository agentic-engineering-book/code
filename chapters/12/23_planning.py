"""Experiment 23 (Chapter 12): Planning."""
import json

from agentic import calculator
from agentic.live import OpenAIModel

PRICES = {"A": 10, "B": 7}  # unit prices in euros


def lookup_price(product):
    return PRICES[product]


TOOLS = {"lookup_price": lookup_price, "calculator": calculator}

planner = OpenAIModel(system="""You are a planner. Tools available:
- lookup_price(product): the unit price of a product, in euros
- calculator(expression): evaluate arithmetic
Reply with a JSON list of steps only, no prose. Each step is
{"tool": ..., "args": {...}, "save_as": ...}; write {name} inside an
argument to use the result an earlier step saved as name.""")


def validate(plan, tools):
    """Reject plans that already contradict known capabilities."""
    problems = []
    for number, step in enumerate(plan, start=1):
        if step["tool"] not in tools:
            problems.append(f"step {number}: no tool {step['tool']!r}")
    return problems


def execute_plan(plan, tools):
    """Run each step; placeholders such as {price_a} name dependencies."""
    state = {}
    for step in plan:
        arguments = {name: str(value).format(**state)
                     for name, value in step["args"].items()}
        state[step["save_as"]] = tools[step["tool"]](**arguments)
    return step, arguments


for goal in ["the total.", "the total in US dollars."]:
    print("GOAL: ...then compute " + goal)
    request = ("Find the price of 3 units of product A and 2 units of "
               "product B, then compute " + goal)
    for trial in range(3):
        reply = planner.generate([{"role": "user", "content": request}])
        plan = json.loads(reply["answer"])
        problems = validate(plan, TOOLS)
        if problems:
            print("  rejected before execution:", problems)
            continue
        last, arguments = execute_plan(plan, TOOLS)
        print(f"  {len(plan)} valid steps; last: {last['save_as']} = "
              f"{arguments['expression']}")
