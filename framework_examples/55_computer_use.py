"""Experiment 55: Computer use in LangGraph. See framework_examples/README."""
import json
from typing import Optional, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel

from framework_examples.support import chat

GOAL = "submit the form"


class ToyScreen:
    """A recorded interface: labelled buttons at pixel centres."""

    def __init__(self):
        self.buttons = {"Submit": (420, 610), "Cancel": (300, 610)}
        self.message = ""

    def observe(self):
        return {"buttons": dict(self.buttons), "message": self.message}

    def dialog_appears(self):  # the layout shifts under the agent
        self.buttons = {"Delete": (420, 610), "Submit": (510, 610),
                        "Cancel": (300, 610)}

    def click(self, point):
        for label, centre in self.buttons.items():
            if centre == point:
                if label == "Submit":
                    self.message = "Submitted successfully"
                return label
        return None


class Point(BaseModel):
    """The centre to click; null coordinates if no control fits."""
    x: Optional[int]
    y: Optional[int]


class State(TypedDict, total=False):
    target: tuple
    pressed: str
    verified: bool


def build(screen, reground):
    model = chat().with_structured_output(Point)

    def ground(state):
        """A real model grounds the goal in the current observation."""
        point = model.invoke(
            f"You control a mouse. Screen: {json.dumps(screen.observe())}"
            f"\nGoal: {GOAL}")
        if point.x is None:
            raise LookupError(f"no control for {GOAL!r}")
        return {"target": (point.x, point.y)}

    def approve(state):  # a human approves; the layout shifts meanwhile
        interrupt({"action": GOAL, "at": state["target"]})
        return {}

    def act(state):
        # The checkpoint stores the tuple as a list; restore it.
        return {"pressed": screen.click(tuple(state["target"]))}

    def verify(state):  # check the postcondition from a NEW observation
        return {"verified":
                screen.observe()["message"] == "Submitted successfully"}

    builder = StateGraph(State)
    for name, node in [("ground", ground), ("approve", approve),
                       ("reground", ground), ("act", act),
                       ("verify", verify)]:
        builder.add_node(name, node)
    builder.add_edge(START, "ground")
    builder.add_edge("ground", "approve")
    builder.add_edge("approve", "reground" if reground else "act")
    builder.add_edge("reground", "act")
    builder.add_edge("act", "verify")
    builder.add_edge("verify", END)
    return builder.compile(checkpointer=InMemorySaver())


def run():
    lines = []
    for label, reground in [("Stale coordinates:", False),
                            ("Re-observe, ground by label, verify:", True)]:
        screen = ToyScreen()
        graph = build(screen, reground)
        config = {"configurable": {"thread_id": label}}
        graph.invoke({}, config)  # pauses at the approval interrupt
        screen.dialog_appears()
        final = graph.invoke(Command(resume=True), config)
        lines.append(label)
        lines.append(f"  click {tuple(final['target'])} -> pressed "
                     f"{final['pressed']!r}")
        lines.append(f"  postcondition verified: {final['verified']}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
