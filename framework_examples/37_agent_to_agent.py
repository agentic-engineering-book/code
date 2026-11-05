"""Experiment 37: A2A task in LangGraph. See framework_examples/README."""
import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from framework_examples.support import chat

FACTS = ("Facts: company A's product costs 80 US dollars; company B's costs "
         "95 US dollars.")
V1 = ("You are a research agent. " + FACTS + ' Reply with JSON only: '
      '{"price": <the lower price as an integer>, "currency": "USD"}.')
V2 = ("You are a research agent. " + FACTS +  # the schema line was dropped
      " Reply with your comparison as JSON only.")
ALLOWED_CALLERS = {"coordinator"}


class Task(TypedDict, total=False):
    caller: str
    text: str
    states: Annotated[list, operator.add]
    artifact: dict


def remote_agent(instructions):
    """A LangGraph task lifecycle; the work is done by a real model."""
    model = chat().bind(response_format={"type": "json_object"})

    def authorize(task):
        allowed = task["caller"] in ALLOWED_CALLERS
        return {"states": ["working" if allowed else "rejected"]}

    def research(task):
        reply = model.invoke([SystemMessage(content=instructions),
                              HumanMessage(content=task["text"])])
        return {"states": ["completed"],
                "artifact": json.loads(reply.content)}

    builder = StateGraph(Task)
    builder.add_node("authorize", authorize)
    builder.add_node("research", research)
    builder.add_edge(START, "authorize")
    builder.add_conditional_edges(
        "authorize",
        lambda task: END if task["states"][-1] == "rejected" else "research")
    builder.add_edge("research", END)
    return builder.compile()


def valid(artifact):
    return (isinstance(artifact.get("price"), int)
            and artifact.get("currency") == "USD")


def run():
    lines = []
    message = {"text": "Compare A and B on price", "states": ["submitted"]}
    for label, instructions, caller in [("v1", V1, "coordinator"),
                                        ("v1", V1, "intruder"),
                                        ("drifted", V2, "coordinator")]:
        task = remote_agent(instructions).invoke({**message, "caller": caller})
        lines.append(f"{label} {caller}: " + " -> ".join(task["states"]))
        if "artifact" in task:
            artifact = task["artifact"]
            lines.append(f"  valid artifact: {valid(artifact)} | "
                         f"first keys: {list(artifact)[:2]}"[:76])
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
