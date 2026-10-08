class Memory:
    def __init__(self): self.items=[]
    def write(self,item,provenance='user'): self.items.append({'value':item,'provenance':provenance})
    def retrieve(self,query,limit=3): return [x for x in self.items if query.lower() in str(x['value']).lower()][:limit]
