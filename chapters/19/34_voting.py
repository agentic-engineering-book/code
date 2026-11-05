"""Experiment 34 (Chapter 19): Voting."""
from collections import Counter

from agentic.live import OpenAIModel

QUESTION = ("Which supplier had the lower defect rate last year, A or B? "
            "Answer A or B only.")
GROUND_TRUTH = "B"
SOURCES = {
    "filing": "Annual filing: last year supplier B's defect rate was 1.2%; "
              "supplier A's was 2.9%.",
    "analyst_note": "Analyst note: B beat A on quality last year, with "
                    "fewer than half A's defects.",
    "promo_blog": "Supplier A blog: A is the quality leader, with the "
                  "lowest defect rates in the industry!",
}


def voter(source):
    """A real model that reads one source and votes."""
    model = OpenAIModel(system="Answer from the source you are given.")
    reply = model.generate([{"role": "user",
                             "content": SOURCES[source] + "\n" + QUESTION}])
    return reply["answer"].strip()[:1]


def majority(votes):
    """Most common answer; an exact tie is reported, not broken at random."""
    ranked = Counter(votes).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "tie"
    return ranked[0][0]


def evaluate(label, sources_read):
    votes = [voter(source) for source in sources_read]
    decision = majority(votes)
    oracle = GROUND_TRUTH in votes  # was at least one voter correct?
    print(f"{label}: votes={votes}")
    print(f"  majority={decision} correct={decision == GROUND_TRUTH} "
          f"oracle@{len(votes)}={oracle} "
          f"unique sources={len(set(sources_read))}")


print(f"ground truth: {GROUND_TRUTH}")
evaluate("independent errors", ["filing", "analyst_note", "promo_blog"])
evaluate("correlated errors", ["promo_blog", "promo_blog", "filing"])
evaluate("nine correlated voters", ["promo_blog"] * 7 + ["filing"] * 2)
evaluate("even split", ["promo_blog", "filing"])
