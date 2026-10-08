"""Experiment 31 (Chapter 17): agent as tool.
Run directly; deterministic by design so the mechanism is inspectable.
"""
def specialist(x): return x*x
def coordinator(x): return specialist(x)
print(coordinator(9))
