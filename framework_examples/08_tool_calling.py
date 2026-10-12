"""Experiment 8: LangChain tool schema and invocation."""
from langchain_core.tools import tool

from agentic.tools import calculator as evaluate


@tool
def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression."""
    return evaluate(expression)


def run():
    # The model sees the name, description and argument schema;
    # the runtime keeps the function.
    return {"name": calculator.name,
            "description": calculator.description,
            "args": calculator.args,
            "result": calculator.invoke({"expression": "18*7"})}


if __name__ == "__main__":
    print(run())
