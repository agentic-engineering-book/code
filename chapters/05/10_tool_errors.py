"""Experiment 10 (Chapter 5): tool errors.
Run directly; deterministic by design so the mechanism is inspectable.
"""

def safe_call(fn,*a):
 try:return {'ok':True,'value':fn(*a)}
 except Exception as e:return {'ok':False,'error':type(e).__name__}
print(safe_call(lambda x:1/x,0))
