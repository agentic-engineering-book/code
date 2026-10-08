"""Experiment 23 (Chapter 12): planning.
Run directly; deterministic by design so the mechanism is inspectable.
"""
goal='publish'; plan=['draft','review','revise','publish']; print(goal,'->',' -> '.join(plan))
