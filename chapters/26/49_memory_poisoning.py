"""Experiment 49 (Chapter 26): memory poisoning.
Run directly; deterministic by design so the mechanism is inspectable.
"""
memory=[{'value':'trusted fact','trusted':True},{'value':'malicious instruction','trusted':False}]; print([x['value'] for x in memory if x['trusted']])
