"""Experiment 23 (Chapter 12): Planning."""
from agentic import calculator

PRICES = {"A": 10, "B": 7}


def lookup_price(product):
    return PRICES[product]


TOOLS = {"lookup_price": lookup_price, "calculator": calculator}

# The goal: price 3 units of A and 2 units of B, then compute the total.
PLAN = [
    {"tool": "lookup_price", "args": {"product": "A"}, "save_as": "A"},
    {"tool": "lookup_price", "args": {"product": "B"}, "save_as": "B"},
    {"tool": "calculator", "args": {"expression": "3*{A} + 2*{B}"},
     "save_as": "total"},
]
BAD_PLAN = PLAN[:2] + [
    {"tool": "currency_converter", "args": {"amount": "{A}"},
     "save_as": "A_usd"},
] + PLAN[2:]


def validate(plan, tools):
    """Reject plans that already contradict known capabilities."""
    problems = []
    for number, step in enumerate(plan, start=1):
        if step["tool"] not in tools:
            problems.append(f"step {number}: no tool {step['tool']!r}")
    return problems


def execute_plan(plan, tools):
    state = {}
    for step in plan:
        # Placeholders such as {A} make each dependency explicit.
        arguments = {name: value.format(**state)
                     for name, value in step["args"].items()}
        result = tools[step["tool"]](**arguments)
        state[step["save_as"]] = result
        print(f"{step['tool']}({arguments}) -> {step['save_as']} = {result}")
    return state


for name, plan in [("plan", PLAN), ("bad plan", BAD_PLAN)]:
    problems = validate(plan, TOOLS)
    if problems:
        print(f"{name}: rejected before execution: {problems}")
        continue
    print(f"{name}: valid, executing")
    print(f"total = {execute_plan(plan, TOOLS)['total']}")
