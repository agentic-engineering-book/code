"""Experiment 22 (Chapter 11): react.
Run directly; deterministic by design so the mechanism is inspectable.
"""
steps=[('thought','need exact arithmetic'),('act','calculator(6*7)'),('observe','42'),('answer','42')]; [print(*s,sep=': ') for s in steps]
