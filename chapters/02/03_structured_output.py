"""Experiment 3 (Chapter 2): structured output.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from dataclasses import dataclass
@dataclass
class Action: tool:str; arguments:dict
a=Action('calculator',{'expression':'6*7'})
if __name__=='__main__': print(a)
