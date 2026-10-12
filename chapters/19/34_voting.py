"""Experiment 34 (Chapter 19): Voting."""
from collections import Counter

GROUND_TRUTH = "B"
SOURCES = {"filing": "B", "analyst_note": "B", "promo_blog": "A"}


def majority(votes):
    """Most common answer; an exact tie is reported, not broken at random."""
    ranked = Counter(votes).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "tie"
    return ranked[0][0]


def evaluate(label, sources_read):
    votes = [SOURCES[source] for source in sources_read]
    decision = majority(votes)
    oracle = GROUND_TRUTH in votes  # was at least one worker correct?
    print(f"{label}: votes={votes}")
    print(f"  majority={decision} correct={decision == GROUND_TRUTH} "
          f"oracle@{len(votes)}={oracle} "
          f"unique sources={len(set(sources_read))}")


print(f"ground truth: {GROUND_TRUTH}")
evaluate("independent errors", ["filing", "analyst_note", "promo_blog"])
evaluate("correlated errors", ["promo_blog", "promo_blog", "filing"])
evaluate("nine correlated voters", ["promo_blog"] * 7 + ["filing"] * 2)
evaluate("even split", ["promo_blog", "filing"])
