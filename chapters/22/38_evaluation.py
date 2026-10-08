"""Experiment 38 (Chapter 22): evaluation.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from agentic.eval import exact_match
print(exact_match('42','42'))
