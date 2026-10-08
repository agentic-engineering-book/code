"""Experiment 26 (Chapter 14): tree reasoning.
Run directly; deterministic by design so the mechanism is inspectable.
"""
candidates=[('A',.5),('B',.9),('C',.4)]; print('expand',max(candidates,key=lambda x:x[1]))
