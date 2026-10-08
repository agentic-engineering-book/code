"""Experiment 36 (Chapter 20): blackboard.
Run directly; deterministic by design so the mechanism is inspectable.
"""
blackboard={}; blackboard['research']='evidence'; blackboard['writer']='draft based on '+blackboard['research']; print(blackboard)
