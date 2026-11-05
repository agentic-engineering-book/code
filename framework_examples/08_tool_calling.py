"""Experiment 8: One tool in LangChain. See framework_examples/README."""
from langchain_core.tools import tool

from agentic.tools import calculator as evaluate
from framework_examples.support import chat


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression exactly. Supports + - * / **."""
    return evaluate(expression)


# The registry: software's source of truth about what can execute.
TOOLS = {"calculator": calculator}


def run():
    # The description (name, docstring, argument schema) goes to the model.
    model = chat().bind_tools(list(TOOLS.values()))
    decision = model.invoke("What is 27611 times 2033?").tool_calls[0]
    result = TOOLS[decision["name"]].invoke(decision["args"])
    return [f"ACTION: {decision['name']} {decision['args']}",
            f"RESULT: {result}"]


if __name__ == "__main__":
    for line in run():
        print(line)
