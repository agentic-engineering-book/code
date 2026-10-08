"""Small visible graph builders shared by the chapter examples.

These helpers build real StateGraphs; node functions remain application code.
Models and environment observations are fixtures, not live services.
"""
from typing import TypedDict, Any, Annotated
import operator
from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    value: Any
    step: int
    results: Annotated[list, operator.add]


def sequence(nodes, initial, *, checkpointer=None, config=None):
    """Named state updates connected in order, with optional checkpointing."""
    builder = StateGraph(State)
    previous = START
    for name, node in nodes:
        builder.add_node(name, node)
        builder.add_edge(previous, name)
        previous = name
    builder.add_edge(previous, END)
    return builder.compile(checkpointer=checkpointer).invoke(initial, config)


def branch(routes, choose, value):
    """A conditional edge chooses a single runnable node."""
    builder = StateGraph(State)
    builder.add_node('route', lambda s: {})
    builder.add_edge(START, 'route')
    for name, node in routes.items():
        builder.add_node(name, node)
        builder.add_edge(name, END)
    builder.add_conditional_edges('route', choose, {n: n for n in routes})
    return builder.compile().invoke({'value': value})['value']


def parallel(workers):
    """Fan out and join reducer-backed results, ordered for repeatable output."""
    builder = StateGraph(State)
    for name, worker in workers.items():
        builder.add_node(name, lambda s, fn=worker, label=name:
                         {'results': [(label, fn())]})
        builder.add_edge(START, name)
    builder.add_node('join', lambda s: {'value': sorted(s['results'])})
    builder.add_edge(list(workers), 'join')
    builder.add_edge('join', END)
    return builder.compile().invoke({'results': []})['value']


def bounded_loop(update, done, initial, limit=20):
    """Application stopping policy plus a framework recursion ceiling."""
    builder = StateGraph(State)
    builder.add_node('step', update)
    builder.add_edge(START, 'step')
    builder.add_conditional_edges('step', lambda s: END if done(s) else 'step')
    return builder.compile().invoke(initial, {'recursion_limit': limit})
