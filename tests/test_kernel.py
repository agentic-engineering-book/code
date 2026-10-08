from agentic import ScriptedModel,Decision,ToolRegistry,calculator,Agent
def test_calculator(): assert calculator('37*42')==1554
def test_agent():
 m=ScriptedModel([Decision(tool='calculator',arguments={'expression':'6*7'}),Decision(done=True,answer='42')])
 assert Agent(m,ToolRegistry(calculator=calculator)).run('6*7?')=='42'
