"""Experiment 4 (Chapter 2): Reject an invalid decision."""
from dataclasses import dataclass
import json

from agentic.live import OpenAIModel


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


model = OpenAIModel(system=(
    'Reply only with JSON: {"action": "<action name>", "arguments": {...}}. '
    "Choose the action that carries out the request. "
    'You have a calculator: {"action": "calculator", '
    '"arguments": {"expression": "<arithmetic expression>"}}'))

requests = ["Work out 27611 times 2033.", "Delete the old customer records."]

for request in requests:
    raw = model.generate([{"role": "user", "content": request}])["answer"]
    print("REQUEST:", request)
    try:
        proposal = json.loads(raw)
        print("PROPOSED:", proposal.get("action"))
        print("ACCEPTED:", validate(proposal))
    except ValueError as error:
        print("BLOCKED:", error)
