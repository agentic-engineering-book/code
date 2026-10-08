"""Experiment 13 (Chapter 7): embeddings.
Run directly; deterministic by design so the mechanism is inspectable.
"""
import math
def emb(s): return [s.lower().count(c) for c in 'agent']
def sim(a,b): return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)) or 1)
print(sim(emb('agent memory'),emb('memory for agents'))) 
