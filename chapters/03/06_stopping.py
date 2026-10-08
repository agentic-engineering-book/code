"""Experiment 6 (Chapter 3): stopping.
Run directly; deterministic by design so the mechanism is inspectable.
"""
MAX_STEPS=3
for step in range(MAX_STEPS): print('working',step+1)
print('stopped by budget')
