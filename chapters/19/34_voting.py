"""Experiment 34 (Chapter 19): voting.
Run directly; deterministic by design so the mechanism is inspectable.
"""
votes=['A','A','B']; print(max(set(votes),key=votes.count))
