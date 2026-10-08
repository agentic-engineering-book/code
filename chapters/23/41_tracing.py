"""Experiment 41 (Chapter 23): tracing.
Run directly; deterministic by design so the mechanism is inspectable.
"""
from agentic.trace import Trace
t=Trace(); t.add('tool_call',tool='calculator'); print(t.events)
