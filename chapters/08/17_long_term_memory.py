"""Experiment 17 (Chapter 8): long term memory.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from agentic.memory import Memory
m=Memory(); m.write('user prefers concise examples'); print(m.retrieve('concise'))
