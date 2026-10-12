"""Experiment 46: LangGraph interrupt bound to an action hash; node replay."""
import hashlib
import json
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict, total=False):
    action: dict
    result: str


def action_hash(action):
    canonical = json.dumps(action, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def run():
    node_runs = []

    def approve_and_send(state):
        node_runs.append("approve_and_send")  # runs again on resume
        digest = action_hash(state["action"])
        decision = interrupt({"action": state["action"], "hash": digest})
        if not decision["approved"] or decision["hash"] != digest:
            return {"result": "blocked"}
        return {"result": "sent"}  # side effects belong after interrupt()

    builder = StateGraph(State)
    builder.add_node("approve_and_send", approve_and_send)
    builder.add_edge(START, "approve_and_send")
    builder.add_edge("approve_and_send", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "approval-demo"}}
    action = {"tool": "send_email", "to": "customer@example.com"}
    paused = graph.invoke({"action": action}, config)
    request = paused["__interrupt__"][0].value
    reviewed = {"approved": True, "hash": request["hash"]}
    final = graph.invoke(Command(resume=reviewed), config)
    return {"paused_for": request["hash"], "result": final["result"],
            "node_runs": len(node_runs)}


if __name__ == "__main__":
    print(run())
