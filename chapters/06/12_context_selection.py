"""Experiment 12 (Chapter 6): context selection.
Run directly; deterministic by design so the mechanism is inspectable.
"""
items=[('relevant',.9),('noise',.1),('old',.2)]; print(sorted(items,key=lambda x:x[1],reverse=True)[:1])
