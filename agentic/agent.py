class Agent:
    def __init__(self,model,tools,max_steps=10): self.model=model; self.tools=tools; self.max_steps=max_steps
    def run(self,goal):
        messages=[{'role':'user','content':goal}]
        for step in range(self.max_steps):
            d=self.model.generate(messages)
            if d.done: return d.answer
            if not d.tool: raise ValueError('decision must finish or choose a tool')
            result=self.tools.call(d.tool,**(d.arguments or {}))
            messages.append({'role':'tool','name':d.tool,'content':str(result)})
        raise RuntimeError('step limit reached')
