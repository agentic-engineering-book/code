"""Experiment 58 (Chapter 30): experience learning.
Run directly; deterministic by design so the mechanism is inspectable.
"""
experience=[('task1','success'),('task2','failure')]; lessons=[x for x in experience if x[1]=='failure']; print('learn from',lessons)
