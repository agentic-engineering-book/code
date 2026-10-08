"""Experiment 55 (Chapter 29): computer use.
Run directly; deterministic by design so the mechanism is inspectable.
"""
screen={'button':(100,200)}; observed=screen['button']; screen['button']=(140,220); print('stale?',observed!=screen['button'])
