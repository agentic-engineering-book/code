"""Experiment 32 (Chapter 18): supervisor workers.
Run directly; deterministic by design so the mechanism is inspectable.
"""
jobs=['research','calculate','write']; print({j:'worker-'+str(i+1) for i,j in enumerate(jobs)})
