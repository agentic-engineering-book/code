"""Experiment 4 (Chapter 2): validation.
Run directly; deterministic by design so the mechanism is inspectable.
"""
def validate(d):
 assert d.get('tool') in {'calculator'}
 assert isinstance(d.get('arguments'),dict)
 return d
if __name__=='__main__': print(validate({'tool':'calculator','arguments':{'expression':'6*7'}}))
