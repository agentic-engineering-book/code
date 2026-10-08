import time
class Trace:
    def __init__(self): self.events=[]
    def add(self,event,**data): self.events.append({'t':time.time(),'event':event,**data})
