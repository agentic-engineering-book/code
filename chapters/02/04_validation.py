"""Experiment 4 (Chapter 2): Reject an invalid decision."""
from dataclasses import dataclass


@dataclass
class CalculatorDecision:
    action: str
    expression: str


def validate(data: dict) -> CalculatorDecision:
    if data.get("action") != "calculator":
        raise ValueError("Unknown action")

    expression = data.get("arguments", {}).get("expression")

    if not isinstance(expression, str):
        raise ValueError("expression must be a string")

    return CalculatorDecision(
        action=data["action"],
        expression=expression,
    )


good = {
    "action": "calculator",
    "arguments": {"expression": "37*42"}
}

bad = {
    "action": "delete_database",
    "arguments": {}
}

print("GOOD:", validate(good))

try:
    validate(bad)
except ValueError as error:
    print("BLOCKED:", error)
