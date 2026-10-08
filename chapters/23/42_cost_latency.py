"""Experiment 42 (Chapter 23): cost latency.
Run directly; deterministic by design so the mechanism is inspectable.
"""
events=[{'cost':.01,'latency':.2},{'cost':.03,'latency':.5}]; print(sum(x['cost'] for x in events),sum(x['latency'] for x in events))
