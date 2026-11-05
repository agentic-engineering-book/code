"""Experiment 34: Voting in LangGraph. See framework_examples/README."""
from collections import Counter

from framework_examples.support import chat, parallel

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
    reply = chat().invoke([("system", "Answer from the source you are given."),
                           ("user", SOURCES[source] + "\n" + QUESTION)])
    return reply.content.strip()[:1]


def majority(votes):
    """Most common answer; an exact tie is reported, not broken at random."""
    ranked = Counter(votes).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "tie"
    return ranked[0][0]


def evaluate(label, sources_read):
    # One LangGraph branch per voter; they run in the same super-step.
    voters = {f"voter_{i}": (lambda s=source: voter(s))
              for i, source in enumerate(sources_read, 1)}
    votes = [vote for _, vote in parallel(voters)]
    decision = majority(votes)
    return [f"{label}: votes={votes}",
            f"  majority={decision} correct={decision == GROUND_TRUTH} "
            f"oracle@{len(votes)}={GROUND_TRUTH in votes} "
            f"unique sources={len(set(sources_read))}"]


def run():
    return [f"ground truth: {GROUND_TRUTH}",
            *evaluate("independent errors",
                      ["filing", "analyst_note", "promo_blog"]),
            *evaluate("correlated errors",
                      ["promo_blog", "promo_blog", "filing"]),
            *evaluate("nine correlated voters",
                      ["promo_blog"] * 7 + ["filing"] * 2),
            *evaluate("even split", ["promo_blog", "filing"])]


if __name__ == "__main__":
    for line in run():
        print(line)
