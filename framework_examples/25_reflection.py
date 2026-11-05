"""Experiment 25: Reflection in LangGraph. See framework_examples/README."""
import re
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from agentic import calculator
from framework_examples.support import chat

TASK = ("A shop buys 417 items at 35 dollars each and sells them at "
        "47 dollars each, but 62 items are unsold. What is the profit "
        "in dollars?")
CORRECT = calculator("355 * 47 - 417 * 35")  # what a tool can confirm
DRAFTS = {5004: "417 * (47 - 35) = 5004 dollars.",
          2090: "355 * 47 - 417 * 35 = 16685 - 14595 = 2090 dollars."}
CRITICS = {
    "careful": "Check this answer step by step, then end with the correct "
               "profit as a line 'FINAL: <integer>'.",
    "hasty": "This answer contains a mistake. Find it and reply with the "
             "corrected profit as a line 'FINAL: <integer>'.",
}
TRIALS = 3


class State(TypedDict, total=False):
    draft: int
    critic: str
    proposed: Optional[int]
    final: int


def critique(state):
    """A real model critic proposes a revised profit."""
    reply = chat().invoke(f"Task: {TASK}\nAnswer: {DRAFTS[state['draft']]}\n"
                          + CRITICS[state["critic"]]).content
    found = re.findall(r"FINAL:\s*\$?([\d,]+)", reply)
    return {"proposed": int(found[-1].replace(",", "")) if found else None}


def gate(state):
    """Revise only if a calculator confirms the proposal."""
    return "revise" if state["proposed"] == CORRECT else "keep"


def build():
    builder = StateGraph(State)
    builder.add_node("critique", critique)
    builder.add_node("revise", lambda s: {"final": s["proposed"]})
    builder.add_node("keep", lambda s: {"final": s["draft"]})
    builder.add_edge(START, "critique")
    builder.add_conditional_edges("critique", gate, ["revise", "keep"])
    builder.add_edge("revise", END)
    builder.add_edge("keep", END)
    return builder.compile()


def outcome(draft, revision):
    if draft != CORRECT:
        return "improvement" if revision == CORRECT else "no useful repair"
    return "preserved" if revision == CORRECT else "REGRESSION"


def run():
    graph = build()
    lines = ["critic   draft  proposed  always            verified"]
    for critic in CRITICS:
        for draft in DRAFTS:
            for trial in range(TRIALS):
                state = graph.invoke({"draft": draft, "critic": critic})
                always = outcome(draft, state["proposed"])
                verified = outcome(draft, state["final"])
                lines.append(f"{critic:8} {draft:>5} {state['proposed']!s:>9}"
                             f"  {always:17} {verified}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
