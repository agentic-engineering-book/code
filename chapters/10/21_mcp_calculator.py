"""Experiment 21 (Chapter 10): mcp calculator.
Run directly; deterministic by design so the mechanism is inspectable.
"""
server={'calculator':lambda expression:eval(expression,{'__builtins__':{}},{})}; print({'discovered':list(server),'result':server['calculator']('6*7')})
