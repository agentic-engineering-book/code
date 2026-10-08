"""Experiment 52 (Chapter 27): autonomy envelope.
Run directly; deterministic by design so the mechanism is inspectable.
"""
envelope={'tools':['search'],'permissions':['read'],'max_steps':20,'max_cost':1.0,'requires_approval':['send_email']}; print(envelope)
