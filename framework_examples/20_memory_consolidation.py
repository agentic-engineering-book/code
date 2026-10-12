"""Experiment 20: LangGraph count-then-consolidate with a conflict guard."""
from framework_examples.support import sequence

MIN_EPISODES = 2


def count(state):
    votes = {}
    for episode in state["value"]:
        text = episode.lower()
        label = ("concise" if "concise" in text or "shorten" in text
                 else "detailed" if "detailed" in text else None)
        if label:
            votes[label] = votes.get(label, 0) + 1
    return {"value": votes}


def consolidate(state):
    votes = state["value"]
    if len(votes) > 1:
        return {"value": f"no fact: conflicting episodes {votes}"}
    if not votes or max(votes.values()) < MIN_EPISODES:
        return {"value": "no fact: not enough evidence"}
    return {"value": f"User prefers {next(iter(votes))} responses."}


def run():
    stages = [("count", count), ("consolidate", consolidate)]
    consistent = ["User requested a concise answer.",
                  "User asked to shorten the explanation.",
                  "User selected the concise version."]
    conflicting = ["User requested a concise answer.",
                   "User requested a detailed technical explanation."]
    return {"consistent": sequence(stages, {"value": consistent})["value"],
            "conflicting": sequence(stages, {"value": conflicting})["value"]}


if __name__ == "__main__":
    print(run())
