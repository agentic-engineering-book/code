"""Experiment 28 (Chapter 15): model routing.
Run directly; deterministic by design so the mechanism is inspectable.
"""
difficulty=.8; model='strong' if difficulty>.6 else 'cheap'; print(model)
