"""Experiment 28: Model routing in LangChain. See framework_examples/README."""
from functools import lru_cache

from langchain_core.runnables import RunnableBranch, RunnableLambda

from agentic import calculator
from framework_examples.support import MODEL, SMALL_MODEL, chat

FAST, STRONG = SMALL_MODEL, MODEL
COST = {FAST: 1, STRONG: 10}  # illustrative units, not prices
# (task, difficulty). Only the oracle reads the labels.
TASKS = [
    ("12 + 30", "easy"),
    ("37 * 43", "easy"),
    ("64 * 25 + 7", "easy"),
    ("(48 - 6) * (9 + 4)", "hard"),
    ("(17 + 8) * (31 - 6)", "hard"),
]


@lru_cache(maxsize=None)  # each model answers each task once
def call_model(model, task):
    reply = chat(model).invoke(f"What is {task}? Reply with the number only.")
    return reply.content.strip().replace(",", "")


def verify(task, answer):
    return answer == str(calculator(task))  # an exact, reliable verifier


def answer_with(model):
    return RunnableLambda(lambda task: {"model": model,
                                        "answer": call_model(model, task),
                                        "task": task})


class VerificationFailed(Exception):
    """Raised when the cheap answer fails the check; triggers escalation."""


def check(result):
    if not verify(result["task"], result["answer"]):
        raise VerificationFailed(result["task"])
    return result


FAST_RUN, STRONG_RUN = answer_with(FAST), answer_with(STRONG)
STRATEGIES = {
    "always fast": FAST_RUN,
    "always strong": STRONG_RUN,
    "oracle": RunnableBranch(  # reads the hidden difficulty label
        (lambda task: dict(TASKS)[task] == "easy", FAST_RUN), STRONG_RUN),
    "length router": RunnableBranch(
        (lambda task: len(task) <= 10, FAST_RUN), STRONG_RUN),
    "cheap-first cascade": (FAST_RUN | RunnableLambda(check)).with_fallbacks(
        [STRONG_RUN], exceptions_to_handle=(VerificationFailed,)),
}


def run():
    lines = []
    for name, strategy in STRATEGIES.items():
        solved, total_cost = 0, 0
        for task, _ in TASKS:
            result = strategy.invoke(task)
            solved += verify(task, result["answer"])
            total_cost += COST[result["model"]]
            if name == "cheap-first cascade" and result["model"] == STRONG:
                total_cost += COST[FAST]  # the failed cheap attempt
        lines.append(f"{name:20} solved {solved}/{len(TASKS)}  "
                     f"cost {total_cost}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
