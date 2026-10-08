"""Experiment 53 (Chapter 28): coding agent.
Run directly; deterministic by design so the mechanism is inspectable.
"""
code='def add(a,b): return a-b'; tests=lambda: (lambda ns: ns['add'](2,3)==5)(exec(code,globals()) or globals()); print('inspect -> edit -> execute -> observe')
