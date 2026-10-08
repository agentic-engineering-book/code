"""Experiment 14 (Chapter 7): rag.
Run directly; deterministic by design so the mechanism is inspectable.
"""
docs=['Paris is in France.','Pretoria is in South Africa.']; q='Pretoria'; evidence=[d for d in docs if q in d]; print('evidence:',evidence)
