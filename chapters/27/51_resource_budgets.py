"""Experiment 51 (Chapter 27): resource budgets.
Run directly; deterministic by design so the mechanism is inspectable.
"""
budget={'steps':3,'cost':.10}; used={'steps':2,'cost':.07}; print(used['steps']<budget['steps'] and used['cost']<budget['cost'])
