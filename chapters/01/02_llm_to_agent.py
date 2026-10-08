"""Experiment 2 (Chapter 1): llm to agent.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from agentic import ScriptedModel, Decision, ToolRegistry, calculator, Agent
m=ScriptedModel([Decision(tool='calculator',arguments={'expression':'37*42'}),Decision(done=True,answer='37 x 42 = 1554.')])
a=Agent(m,ToolRegistry(calculator=calculator))
if __name__=='__main__': print(a.run('What is 37 x 42?'))
