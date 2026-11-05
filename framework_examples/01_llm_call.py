"""Experiment 1: A model call in LangChain. See framework_examples/README."""
from framework_examples.support import chat

QUESTION = "What is 27611 * 2033? Reply with the number only."


def run():
    answer = chat().invoke(QUESTION).content
    correct = str(27611 * 2033) in answer.replace(",", "")
    return [f"MODEL: {' '.join(answer.split())[:60]}",
            f"GROUND TRUTH: {27611 * 2033}",
            f"CORRECT: {correct}"]


if __name__ == "__main__":
    for line in run():
        print(line)
