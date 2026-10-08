"""Experiment 39 (Chapter 22): trajectory eval.
Run directly; deterministic by design so the mechanism is inspectable.
"""
trajectory=['search','calculator','answer']; allowed={'search','calculator','answer'}; print(all(x in allowed for x in trajectory))
