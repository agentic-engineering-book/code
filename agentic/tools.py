import ast, operator as op
OPS={ast.Add:op.add,ast.Sub:op.sub,ast.Mult:op.mul,ast.Div:op.truediv,ast.Pow:op.pow,ast.USub:op.neg}
def _eval(n):
    if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
    if isinstance(n,ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](_eval(n.left),_eval(n.right))
    if isinstance(n,ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](_eval(n.operand))
    raise ValueError('unsupported expression')
def calculator(expression:str): return _eval(ast.parse(expression,mode='eval').body)
class ToolRegistry(dict):
    def call(self,name,**kwargs): return self[name](**kwargs)
