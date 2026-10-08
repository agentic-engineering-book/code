"""Experiment 35 (Chapter 19): debate judge.
Run directly; deterministic by design so the mechanism is inspectable.
"""
arguments={'agent_a':'A','agent_b':'B'}; judge=lambda a:'A' if 'A' in a.values() else 'B'; print(judge(arguments))
