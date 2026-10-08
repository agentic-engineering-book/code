"""Experiment 46 (Chapter 25): human approval.
Run directly; deterministic by design so the mechanism is inspectable.
"""
action={'tool':'send_email','approved':False}; print('execute' if action['approved'] else 'WAIT FOR HUMAN')
