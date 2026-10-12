"""Experiment 38: LangChain batch evaluation with exact and numeric match."""
from langchain_core.runnables import RunnableLambda

CASES = [("17 * 6", 102), ("25 + 19", 44), ("81 / 9", 9)]
FIXTURE_ANSWERS = {"17 * 6": "102", "25 + 19": "45", "81 / 9": "9.0"}


def numeric_match(answer, expected):
    try:
        return abs(float(answer) - expected) < 1e-9
    except ValueError:
        return False


def run():
    agent = RunnableLambda(lambda question: FIXTURE_ANSWERS[question])
    answers = agent.batch([question for question, _ in CASES])
    expected = [value for _, value in CASES]
    exact = sum(a == e for a, e in zip(answers, expected))
    numeric = sum(numeric_match(a, e) for a, e in zip(answers, expected))
    return {"cases": len(CASES), "exact_match": exact,
            "numeric_match": numeric}


if __name__ == "__main__":
    print(run())
