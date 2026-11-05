"""Experiment 46: Human approval, LangGraph. See framework_examples/README."""
import hashlib
import json
from typing import TypedDict

from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from framework_examples.support import chat

REQUEST = ("Email our proposal summary to customer@example.com: the new "
           "plan costs 40 dollars a month and starts in June.")
APPROVAL_TTL_MINUTES = 15


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return "sent"


class State(TypedDict, total=False):
    action: dict
    result: str


def action_hash(action):
    """Stable across processes: SHA-256 of canonical JSON."""
    canonical = json.dumps(action, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def propose(state):
    """A real agent proposes the tool call; nothing is executed here."""
    model = chat().bind_tools([send_email], tool_choice="required")
    call = model.invoke(REQUEST).tool_calls[0]
    return {"action": {"tool": call["name"], "args": call["args"]}}


def approve_and_send(state):
    """Re-runs from the top on resume: side effects go after interrupt()."""
    digest = action_hash(state["action"])
    decision = interrupt({"hash": digest, "state": "AWAITING_APPROVAL"})
    if not decision["approved"]:
        return {"result": "blocked: not approved"}
    if decision["minutes_waited"] > APPROVAL_TTL_MINUTES:
        return {"result": "blocked: approval expired"}
    if decision["hash"] != digest:
        return {"result": "blocked: action changed after approval"}
    return {"result": send_email.invoke(state["action"]["args"])}


def run():
    builder = StateGraph(State)
    builder.add_node("propose", propose)
    builder.add_node("approve_and_send", approve_and_send)
    builder.add_edge(START, "propose")
    builder.add_edge("propose", "approve_and_send")
    builder.add_edge("approve_and_send", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    lines = []
    for label, approved, minutes, mutate in [
            ("rejected", False, 2, False), ("approved", True, 2, False),
            ("mutated recipient", True, 2, True),
            ("two hours later", True, 120, False)]:
        config = {"configurable": {"thread_id": label}}
        paused = graph.invoke({}, config)
        request = paused["__interrupt__"][0].value
        if not lines:
            action = graph.get_state(config).values["action"]
            lines += [f"agent proposes: {action['tool']} to "
                      f"{action['args']['to']}",
                      f"paused: {request['state']} {request['hash']}"]
        if mutate:  # the stored action changes after the human looked
            action = graph.get_state(config).values["action"]
            args = {**action["args"], "to": "all-customers@example.com"}
            graph.update_state(config, {"action": {**action, "args": args}})
        decision = {"approved": approved, "hash": request["hash"],
                    "minutes_waited": minutes}
        final = graph.invoke(Command(resume=decision), config)
        lines.append(f"{label}: {final['result']}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
