"""Experiment 38 (Chapter 22): Task evaluation."""
from agentic.eval import exact_match, numeric_match, success_rate

CASES = [
    ("17 * 6", 102),
    ("25 + 19", 44),
    ("81 / 9", 9),
]

# A fixture agent that answers in text, as a language model does.
# One answer is wrong; one is right but formatted as "9.0".
FIXTURE_ANSWERS = {"17 * 6": "102", "25 + 19": "45", "81 / 9": "9.0"}


def agent(question):
    return FIXTURE_ANSWERS[question]


def evaluate(agent, cases, compare):
    results = []
    for question, expected in cases:
        answer = agent(question)
        results.append(compare(answer, expected))
    return results


for compare in (exact_match, numeric_match):
    results = evaluate(agent, CASES, compare)
    print(f"{compare.__name__:<13} {sum(results)}/{len(results)} correct "
          f"(success rate {success_rate(results):.2f})")
