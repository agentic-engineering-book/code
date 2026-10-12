"""Experiment 1 (Chapter 1): A model call."""
from agentic.model import ScriptedModel

model = ScriptedModel([
    "37 x 42 is approximately 1,500."
])

messages = [
    {"role": "user", "content": "What is 37 * 42?"}
]

answer = model.generate(messages)

print("MODEL:", answer)
print("GROUND TRUTH:", 37 * 42)
print("CORRECT:", str(37 * 42) in answer)
