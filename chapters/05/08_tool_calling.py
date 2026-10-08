"""Experiment 8 (Chapter 5): tool calling.
Run directly; deterministic by design so the mechanism is inspectable.
"""
tools={'add':lambda a,b:a+b}; print(tools['add'](2,3))
