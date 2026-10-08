"""Experiment 27 (Chapter 15): routing.
Run directly; deterministic by design so the mechanism is inspectable.
"""
task='calculate'; routes={'calculate':'math_agent','write':'writer'}; print(routes[task])
