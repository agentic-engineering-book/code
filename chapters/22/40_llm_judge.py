"""Experiment 40 (Chapter 22): llm judge.
Run directly; deterministic by design so the mechanism is inspectable.
"""
rubric=lambda answer: 1 if answer.strip()=='42' else 0; print(rubric('42'))
