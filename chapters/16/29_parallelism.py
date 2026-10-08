"""Experiment 29 (Chapter 16): parallelism.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor() as ex: print(list(ex.map(lambda x:x*x,[2,3,4])))
