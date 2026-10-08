"""Experiment 59 (Chapter 30): reward optimization.
Run directly; deterministic by design so the mechanism is inspectable.
"""
reward=lambda correct,cost: correct-0.1*cost; policies={'long':reward(1,5),'short':reward(.9,1)}; print(max(policies,key=policies.get),policies)
