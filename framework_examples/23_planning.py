"""Experiment 23: Plan, validate, execute in LangChain. See README."""
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from agentic import calculator
from framework_examples.support import chat

PRICES = {"A": 10, "B": 7}  # unit prices in euros
TOOLS = {"lookup_price": lambda product: PRICES[product],
         "calculator": calculator}
PLANNER = """You are a planner. Tools available:
- lookup_price(product): the unit price of a product, in euros
- calculator(expression): evaluate arithmetic
Reply with a JSON list of steps only, no prose. Each step is
{{"tool": ..., "args": {{...}}, "save_as": ...}}; write {{name}} inside an
argument to use the result an earlier step saved as name."""
REQUEST = ("Find the price of 3 units of product A and 2 units of "
           "product B, then compute {goal}")


def validate(plan):
    """Reject plans that already contradict known capabilities."""
    return {"plan": plan, "problems": [
        f"step {n}: no tool {step['tool']!r}"
        for n, step in enumerate(plan, start=1) if step["tool"] not in TOOLS]}


def execute(checked):
    """Run each step; placeholders such as {price_a} name dependencies."""
    if checked["problems"]:
        return ("  rejected before execution: "
                + "; ".join(checked["problems"]))[:76]
    state = {}
    for step in checked["plan"]:
        arguments = {name: str(value).format(**state)
                     for name, value in step["args"].items()}
        state[step["save_as"]] = TOOLS[step["tool"]](**arguments)
    return (f"  {len(checked['plan'])} valid steps; last: "
            f"{step['save_as']} = {arguments.get('expression', '')}")


def run():
    planner = (ChatPromptTemplate.from_messages([("system", PLANNER),
                                                 ("human", REQUEST)])
               | chat() | JsonOutputParser())
    chain = planner | RunnableLambda(validate) | RunnableLambda(execute)
    lines = []
    for goal in ["the total.", "the total in US dollars."]:
        lines.append("GOAL: ...then compute " + goal)
        lines += chain.batch([{"goal": goal}] * 3)
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
