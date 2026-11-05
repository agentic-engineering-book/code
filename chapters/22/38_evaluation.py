"""Experiment 38 (Chapter 22): Task evaluation."""
from agentic.eval import exact_match, numeric_match, success_rate
from agentic.live import OpenAIModel

CASES = [
    ("17 * 6", 102),
    ("25 + 19", 44),
    ("81 / 9", 9),
    ("4817 * 263", 1266871),
]
model = OpenAIModel()


def agent(question):
    """A real model answering without tools, in text."""
    reply = model.generate([{"role": "user", "content":
                             f"What is {question}? Reply with the number "
                             "only."}])
    return reply["answer"].strip()


answers = [(agent(question), expected) for question, expected in CASES]
print("answers:", [answer for answer, expected in answers])
for compare in (exact_match, numeric_match):
    results = [compare(answer, expected) for answer, expected in answers]
    print(f"{compare.__name__:<13} {sum(results)}/{len(results)} correct "
          f"(success rate {success_rate(results):.2f})")
