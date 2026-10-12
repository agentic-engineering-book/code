"""Experiment 28: Cheap-first model cascade with LangChain fallbacks."""
from langchain_core.runnables import RunnableLambda

from agentic import calculator

COST = {"fast_model": 1, "strong_model": 10}
TASKS = [("12 + 30", "easy"), ("17 * 6", "easy"),
         ("(48 - 6) * (9 + 4)", "hard"), ("99 * 99", "hard")]


def fast_model(task):
    """Assumption: the fast model is wrong on hard tasks."""
    expression, difficulty = task
    error = 1 if difficulty == "hard" else 0
    return {"model": "fast_model", "answer": calculator(expression) + error,
            "task": task}


def strong_model(task):
    return {"model": "strong_model", "answer": calculator(task[0]),
            "task": task}


class VerificationFailed(Exception):
    """Raised when the cheap answer fails the check; triggers escalation."""


def verify(result):
    """Exact verifier: only this exception escalates to the strong model."""
    if result["answer"] != calculator(result["task"][0]):
        raise VerificationFailed(result["task"][0])
    return result


def run():
    fast_then_verify = RunnableLambda(fast_model) | RunnableLambda(verify)
    cascade = fast_then_verify.with_fallbacks(
        [RunnableLambda(strong_model)],
        exceptions_to_handle=(VerificationFailed,))
    routed, cost = [], 0
    for task in TASKS:
        result = cascade.invoke(task)
        escalated = result["model"] == "strong_model"
        cost += COST["fast_model"]
        if escalated:
            cost += COST["strong_model"]
        routed.append([task[0], result["model"], result["answer"]])
    return {"routed": routed, "cost": cost}


if __name__ == "__main__":
    print(run())
