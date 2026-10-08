"""Experiment 57 (Chapter 30): self improvement.
Run directly; deterministic by design so the mechanism is inspectable.
"""
prompts=['answer quickly','answer and verify']; scores=[.6,.9]; print(prompts[scores.index(max(scores))])
