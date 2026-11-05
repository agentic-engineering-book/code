"""Experiment 20: Memory consolidation as a LangGraph graph. See README."""
import textwrap
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from framework_examples.support import chat

PLAIN = ("Write one durable fact about the user's preferences, based on "
         "these past episodes. Reply with the fact only.")
GUARDED = PLAIN + (" If fewer than two episodes support it, or the "
                   "episodes conflict, reply NONE.")
MIN_EPISODES = 2
EPISODES = {
    "CONSISTENT": ["User requested a concise answer.",
                   "User asked to shorten the explanation.",
                   "User selected the concise version."],
    "CONFLICTING": ["User requested a concise answer.",
                    "User requested a detailed technical explanation."],
    "ONE EPISODE": ["User requested a concise answer."],
}


class State(TypedDict, total=False):
    episodes: list
    fact: str


def consolidate(system):
    model = chat()
    return lambda state: {"fact": model.invoke(
        [("system", system), ("human", "\n".join(state["episodes"]))]
    ).content}


def checked():
    """The threshold is counted in code; the model judges the conflict."""
    builder = StateGraph(State)
    builder.add_node("too_few", lambda state: {
        "fact": "NONE (not enough episodes)"})
    builder.add_node("consolidate", consolidate(GUARDED))
    builder.add_conditional_edges(
        START, lambda s: "consolidate" if len(s["episodes"])
        >= MIN_EPISODES else "too_few", ["consolidate", "too_few"])
    builder.add_edge("consolidate", END)
    builder.add_edge("too_few", END)
    return builder.compile().invoke


def run():
    variants = {"plain": consolidate(PLAIN), "guarded": consolidate(GUARDED),
                "checked": checked()}
    lines = []
    for label, episodes in EPISODES.items():
        lines.append(label)
        for name, variant in variants.items():
            fact = variant({"episodes": episodes})["fact"]
            lines += textwrap.wrap(fact, 76, initial_indent=f"  {name:<8} ",
                                   subsequent_indent=" " * 11)
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
