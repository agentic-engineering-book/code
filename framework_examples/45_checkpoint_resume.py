"""Experiment 45: LangGraph checkpoint and continuation. See framework_examples/README.md."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict


def run():
    class State(TypedDict):
        step: int
    builder = StateGraph(State)
    builder.add_node('first', lambda s: {'step': 1})
    builder.add_node('second', lambda s: {'step': 2})
    builder.add_edge(START, 'first'); builder.add_edge('first', 'second'); builder.add_edge('second', END)
    app = builder.compile(checkpointer=InMemorySaver(), interrupt_before=['second'])
    config = {'configurable': {'thread_id': 'resume-demo'}}
    app.invoke({'step': 0}, config)
    paused = app.get_state(config).values['step']
    completed = app.invoke(None, config)['step']
    return [paused, completed]


if __name__ == "__main__":
    print(run())
