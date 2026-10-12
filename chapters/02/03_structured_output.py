"""Experiment 3 (Chapter 2): Structured output."""
import json

raw = '{"action":"calculator","arguments":{"expression":"37*42"}}'
decision = json.loads(raw)

print("ACTION:", decision["action"])
print("ARGUMENTS:", decision["arguments"])
