"""Experiment 24 (Chapter 12): plan execute.
Run directly; deterministic by design so the mechanism is inspectable.
"""
plan=['search','summarize']; observations={'search':'new evidence'}; [print('execute',x,'=>',observations.get(x,'ok')) for x in plan]
