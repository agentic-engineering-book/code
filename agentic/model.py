from dataclasses import dataclass
from typing import Any

@dataclass
class Decision:
    done: bool=False
    answer: str|None=None
    tool: str|None=None
    arguments: dict[str,Any]|None=None

class ScriptedModel:
    """Deterministic model used to isolate architecture from model variance."""
    def __init__(self, decisions): self.decisions=list(decisions); self.i=0
    def generate(self, messages):
        d=self.decisions[min(self.i,len(self.decisions)-1)]; self.i+=1; return d
