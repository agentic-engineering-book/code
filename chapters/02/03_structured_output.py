"""Experiment 3 (Chapter 2): Structured output."""
import json

from agentic.live import OpenAIModel

model = OpenAIModel(system=(
    'Reply only with JSON: {"action": "calculator", '
    '"arguments": {"expression": "<arithmetic expression>"}}'))

request = "Work out 27611 times 2033."
raw = model.generate([{"role": "user", "content": request}])["answer"]
decision = json.loads(raw)

print("RAW:", raw)
print("ACTION:", decision["action"])
print("ARGUMENTS:", decision["arguments"])
