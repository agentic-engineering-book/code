"""Experiment 35 (Chapter 19): Judge and debate."""
from agentic import calculator

QUESTION = "17 * 6"

DEBATE = {
    "A": {"answer": 96, "argument": "17 * 6 is 96."},
    "B": {"answer": 102, "argument": "Check by decomposition: "
                                     "10*6 + 7*6 = 60 + 42 = 102."},
}
PERSUASION = {
    "A": {"answer": 96, "argument": "Clearly and without any doubt the "
                                    "answer is 96; every careful reader "
                                    "will confirm this obvious result."},
    "B": {"answer": 102, "argument": "102."},
}


def rhetoric_judge(candidates):
    """Stand-in for an unverified judge: the longest argument wins."""
    return max(candidates, key=lambda n: len(candidates[n]["argument"]))


def grounded_judge(candidates):
    """Checks each claim with a tool; refuses to force a resolution."""
    truth = calculator(QUESTION)
    verified = [n for n, c in candidates.items() if c["answer"] == truth]
    return verified[0] if verified else "no candidate verified"


for label, candidates in [("debate", DEBATE), ("persuasion", PERSUASION)]:
    print(f"{label}:")
    for judge in (rhetoric_judge, grounded_judge):
        choice = judge(candidates)
        answer = candidates.get(choice, {}).get("answer")
        correct = answer == calculator(QUESTION)
        print(f"  {judge.__name__}: {choice} -> {answer} correct={correct}")
