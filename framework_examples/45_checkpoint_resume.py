"""Experiment 45: Checkpoints in LangGraph. See framework_examples/README."""
import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from framework_examples.support import chat

STEPS = ["retrieve", "analyze", "draft", "verify", "submit"]


class State(TypedDict):
    source_version: int
    done: Annotated[list, operator.add]


def build(source, executed, crash_at):
    """A graph whose every step is a real model call."""
    model = chat()

    def step(name):
        def node(state):
            if crash_at.pop(name, False):
                raise RuntimeError(f"crash during {name}")
            model.invoke(f"Task T42: the price is {source['price']}. "
                         f"Do the '{name}' step in at most eight words.")
            executed.append(name)
            return {"done": [name]}
        return node

    builder = StateGraph(State)
    previous = START
    for name in STEPS:
        builder.add_node(name, step(name))
        builder.add_edge(previous, name)
        previous = name
    builder.add_edge(previous, END)
    return builder.compile(checkpointer=InMemorySaver())


def scenario(source_changes):
    source, executed, lines = {"price": 80, "version": 4}, [], []
    graph = build(source, executed, {"verify": True})
    config = {"configurable": {"thread_id": "task-T42"}}
    try:
        graph.invoke({"source_version": source["version"], "done": []},
                     config)
    except RuntimeError as error:
        lines.append(f"first run: {error}, after {len(executed)} "
                     "model calls")
    if source_changes:
        source.update(price=90, version=5)  # changed while we were down
    executed.clear()
    saved = graph.get_state(config).values
    if saved["source_version"] != source["version"]:
        lines.append("  stale checkpoint: source changed, restarting")
        config = {"configurable": {"thread_id": "task-T42-v5"}}
        graph.invoke({"source_version": source["version"], "done": []},
                     config)
    else:
        graph.invoke(None, config)  # resume from the last checkpoint
    lines.append(f"resume: {', '.join(executed)} "
                 f"({len(executed)} model calls)")
    return lines


def run():
    return scenario(source_changes=False) + scenario(source_changes=True)


if __name__ == "__main__":
    for line in run():
        print(line)
