"""Experiment 15 (Chapter 7): reranking.
Run directly; deterministic by design so the mechanism is inspectable.
"""
candidates=[('keyword match',.6),('direct answer',.95)]; print(max(candidates,key=lambda x:x[1]))
