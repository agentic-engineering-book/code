from dataclasses import dataclass
@dataclass
class Budget:
    max_steps:int=10; max_cost:float=1.0; timeout_s:float=120.0
@dataclass
class Permission:
    capability:str; allowed:bool=True; requires_approval:bool=False
