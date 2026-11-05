"""Experiment 3: Structured output. See framework_examples/README."""
from typing import Literal

from pydantic import BaseModel

from framework_examples.support import chat


class Arguments(BaseModel):
    expression: str


class CalculatorDecision(BaseModel):
    """A call to the calculator with an arithmetic expression."""
    action: Literal["calculator"]
    arguments: Arguments


def run():
    # The provider constrains generation to the Pydantic schema.
    model = chat().with_structured_output(CalculatorDecision,
                                          include_raw=True)
    result = model.invoke("Work out 27611 times 2033.")
    decision = result["parsed"]
    return [f"RAW: {result['raw'].content}",
            f"ACTION: {decision.action}",
            f"ARGUMENTS: {decision.arguments.model_dump()}"]


if __name__ == "__main__":
    for line in run():
        print(line)
