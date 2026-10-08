"""Experiment 54 (Chapter 28): iterative repair.
Run directly; deterministic by design so the mechanism is inspectable.
"""
candidate='return a-b'; feedback='test failed'; repaired='return a+b'; print(candidate,'=>',feedback,'=>',repaired)
