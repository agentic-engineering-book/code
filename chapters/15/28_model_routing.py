"""Experiment 28 (Chapter 15): Model routing."""
from agentic import calculator
from agentic.live import OpenAIModel

FAST, STRONG = "gpt-5.4-nano-2026-03-17", "gpt-5.4-mini-2026-03-17"
COST = {FAST: 1, STRONG: 10}  # illustrative units, not prices
# (task, difficulty). Measured beforehand: FAST failed every trial on the
# hard tasks and none on the easy ones. Only the oracle reads the labels.
TASKS = [
    ("12 + 30", "easy"),
    ("37 * 43", "easy"),
    ("64 * 25 + 7", "easy"),
    ("(48 - 6) * (9 + 4)", "hard"),
    ("(17 + 8) * (31 - 6)", "hard"),
]


def call_model(model, task):
    reply = OpenAIModel(model).generate([{"role": "user", "content":
                                          f"What is {task}? Reply with the "
                                          "number only."}])
    return reply["answer"].strip().replace(",", "")


def verify(task, answer):
    return answer == str(calculator(task))    # an exact, reliable verifier


def choose_model(task):
    """Observable feature: long expressions are predicted to be hard."""
    return FAST if len(task) <= 10 else STRONG


def single_route(pick):
    def strategy(task, difficulty):
        model = pick(task, difficulty)
        return call_model(model, task), COST[model]
    return strategy


def cascade(task, difficulty):
    answer, cost = call_model(FAST, task), COST[FAST]
    if not verify(task, answer):                  # escalate on failure
        answer = call_model(STRONG, task)
        cost += COST[STRONG]
    return answer, cost


STRATEGIES = {
    "always fast": single_route(lambda task, difficulty: FAST),
    "always strong": single_route(lambda task, difficulty: STRONG),
    "oracle": single_route(
        lambda task, difficulty: FAST if difficulty == "easy" else STRONG),
    "length router": single_route(
        lambda task, difficulty: choose_model(task)),
    "cheap-first cascade": cascade,
}

for name, strategy in STRATEGIES.items():
    solved, total_cost = 0, 0
    for task, difficulty in TASKS:
        answer, cost = strategy(task, difficulty)
        solved += verify(task, answer)
        total_cost += cost
    print(f"{name:20} solved {solved}/{len(TASKS)}  cost {total_cost}")
