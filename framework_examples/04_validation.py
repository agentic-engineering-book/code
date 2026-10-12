"""Experiment 4: LangChain tool argument validation."""
from langchain_core.tools import tool
from pydantic import ValidationError

from agentic.tools import calculator as evaluate


@tool
def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression."""
    return evaluate(expression)


def run():
    rejected = False
    try:
        # Valid JSON, wrong shape: the expression must be a string.
        calculator.invoke({"expression": ["37", "*", "42"]})
    except ValidationError:
        rejected = True
    return {"valid": calculator.invoke({"expression": "37*42"}),
            "list_expression_rejected": rejected}


if __name__ == "__main__":
    print(run())
