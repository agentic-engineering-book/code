"""Experiment 23: Plan, validate, execute as LangChain runnables."""
from langchain_core.runnables import RunnableLambda

from agentic import calculator

PRICES = {"A": 10, "B": 7}
TOOLS = {"lookup_price": lambda product: PRICES[product],
         "calculator": calculator}
GOOD = [
    {"tool": "lookup_price", "args": {"product": "A"}, "save_as": "A"},
    {"tool": "lookup_price", "args": {"product": "B"}, "save_as": "B"},
    {"tool": "calculator", "args": {"expression": "3*{A} + 2*{B}"},
     "save_as": "total"},
]
BAD = GOOD[:2] + [{"tool": "currency_converter", "args": {},
                   "save_as": "A_usd"}] + GOOD[2:]


def plan(goal):
    """Scripted planner: the 'convert' goal adds an unavailable tool."""
    return {"goal": goal, "steps": BAD if "convert" in goal else GOOD}


def validate(planned):
    missing = [s["tool"] for s in planned["steps"] if s["tool"] not in TOOLS]
    return {**planned, "problems": missing}


def execute(planned):
    if planned["problems"]:
        return {"status": "rejected", "unknown_tools": planned["problems"]}
    state = {}
    for step in planned["steps"]:
        args = {k: v.format(**state) for k, v in step["args"].items()}
        state[step["save_as"]] = TOOLS[step["tool"]](**args)
    return {"status": "done", "state": state}


def run():
    chain = (RunnableLambda(plan) | RunnableLambda(validate)
             | RunnableLambda(execute))
    return chain.batch(["total for 3 A and 2 B",
                        "convert, then total for 3 A and 2 B"])


if __name__ == "__main__":
    print(run())
