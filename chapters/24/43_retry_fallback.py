"""Experiment 43 (Chapter 24): retry fallback.
Run directly; deterministic by design so the mechanism is inspectable.
"""
attempts=0
while attempts<3:
 attempts+=1
 if attempts==2: print('success on',attempts); break
 print('retry',attempts)
