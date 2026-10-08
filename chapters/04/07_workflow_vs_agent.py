"""Experiment 7 (Chapter 4): workflow vs agent.
Run directly; deterministic by design so the mechanism is inspectable.
"""
def workflow(x): return x*2
def agent(x): return ('double' if x<10 else 'square', x*2 if x<10 else x*x)
if __name__=='__main__': print(workflow(4),agent(12))
