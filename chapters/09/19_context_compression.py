"""Experiment 19 (Chapter 9): context compression.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from agentic.context import compress
print(compress('observation '*40,80))
