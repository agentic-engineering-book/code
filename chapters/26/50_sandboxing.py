"""Experiment 50 (Chapter 26): sandboxing.
Run directly; deterministic by design so the mechanism is inspectable.
"""
allowed={'read_fixture'}; requested='shell'; print('allowed?',requested in allowed)
