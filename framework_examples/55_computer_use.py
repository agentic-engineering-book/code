"""Experiment 55: LangGraph approve -> re-ground -> act -> verify workflow."""
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

SCREEN = {"buttons": {"Submit": (420, 610), "Cancel": (300, 610)},
          "message": ""}


def shift_layout():  # a dialog appears while the human is deciding
    SCREEN["buttons"] = {"Delete": (420, 610), "Submit": (510, 610),
                         "Cancel": (300, 610)}


class State(TypedDict):
    target: tuple
    clicked: str
    verified: bool


def ground(state):
    return {"target": SCREEN["buttons"]["Submit"]}


def approve(state):
    approved = interrupt({"action": "click Submit", "at": state["target"]})
    if not approved:
        return Command(goto=END)
    return {}


def act(state):
    for label, centre in SCREEN["buttons"].items():
        if centre == state["target"]:
            if label == "Submit":
                SCREEN["message"] = "Submitted successfully"
            return {"clicked": label}
    return {"clicked": "nothing"}


def verify(state):
    return {"verified": SCREEN["message"] == "Submitted successfully"}


def run():
    SCREEN.update(buttons={"Submit": (420, 610), "Cancel": (300, 610)},
                  message="")
    builder = StateGraph(State)
    for name, node in [("ground", ground), ("approve", approve),
                       ("reground", ground), ("act", act),
                       ("verify", verify)]:
        builder.add_node(name, node)
    builder.add_edge(START, "ground")
    builder.add_edge("ground", "approve")
    # Never act on coordinates grounded before the approval wait.
    builder.add_edge("approve", "reground")
    builder.add_edge("reground", "act")
    builder.add_edge("act", "verify")
    builder.add_edge("verify", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "submit-form"}}
    paused = graph.invoke({"clicked": "", "verified": False}, config)
    first_target = paused["target"]
    shift_layout()
    final = graph.invoke(Command(resume=True), config)
    return {"grounded_before_approval": list(first_target),
            "clicked_at": list(final["target"]),
            "clicked": final["clicked"], "verified": final["verified"]}


if __name__ == "__main__":
    print(run())
