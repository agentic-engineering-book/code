"""Experiment 45: LangGraph checkpoints let a failed run resume mid-graph."""
import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

STEPS = ["retrieve", "analyze", "draft", "verify", "submit"]


class State(TypedDict):
    done: Annotated[list, operator.add]


def run():
    executions = []
    crash = {"verify": True}  # verify fails once, as if the process died

    def step(name):
        def node(state):
            executions.append(name)
            if crash.pop(name, False):
                raise RuntimeError(f"crash during {name}")
            return {"done": [name]}
        return node

    builder = StateGraph(State)
    previous = START
    for name in STEPS:
        builder.add_node(name, step(name))
        builder.add_edge(previous, name)
        previous = name
    builder.add_edge(previous, END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "task-T42"}}
    try:
        graph.invoke({"done": []}, config)
    except RuntimeError:
        pass
    first_run = list(executions)
    final = graph.invoke(None, config)  # resume from the last checkpoint
    return {"first_run": first_run,
            "resumed": executions[len(first_run):],
            "done": final["done"]}


if __name__ == "__main__":
    print(run())
