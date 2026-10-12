"""Experiment 34: LangGraph parallel voters with an explicit vote policy."""
from collections import Counter

from framework_examples.support import parallel

GROUND_TRUTH = "B"
SOURCES = {"filing": "B", "analyst_note": "B", "promo_blog": "A"}


def majority(votes):
    ranked = Counter(votes).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "tie"  # escalate instead of breaking ties arbitrarily
    return ranked[0][0]


def vote(sources_read):
    voters = {f"voter_{i}": (lambda s=source: SOURCES[s])
              for i, source in enumerate(sources_read, 1)}
    votes = [answer for _, answer in parallel(voters)]
    decision = majority(votes)
    return {"votes": votes, "majority": decision,
            "correct": decision == GROUND_TRUTH,
            "unique_sources": len(set(sources_read))}


def run():
    return {
        "independent": vote(["filing", "analyst_note", "promo_blog"]),
        "correlated": vote(["promo_blog", "promo_blog", "filing"]),
        "split": vote(["promo_blog", "filing"]),
    }


if __name__ == "__main__":
    print(run())
