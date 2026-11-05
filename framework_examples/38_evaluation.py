"""Experiment 38: Task evaluation, LangChain. See framework_examples/README."""
from agentic.eval import exact_match, numeric_match, success_rate
from framework_examples.support import chat

CASES = [("17 * 6", 102), ("25 + 19", 44), ("81 / 9", 9),
         ("4817 * 263", 1266871)]


def run():
    questions = [f"What is {q}? Reply with the number only." for q, _ in CASES]
    answers = [reply.content.strip() for reply in chat().batch(questions)]
    lines = [f"answers: {answers}"]
    for compare in (exact_match, numeric_match):
        results = [compare(answer, expected)
                   for answer, (_, expected) in zip(answers, CASES)]
        lines.append(f"{compare.__name__:<13} {sum(results)}/{len(results)} "
                     f"correct (success rate {success_rate(results):.2f})")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
