"""Experiment 9 (Chapter 5): multiple tools.
Run directly; deterministic by design so the mechanism is inspectable.
"""
tools={'add':lambda a,b:a+b,'max':max}; choice='max'; print(tools[choice](2,7))
