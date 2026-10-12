"""Experiment 28 (Chapter 15): Model routing."""
from agentic import calculator

FAST, STRONG = "fast_model", "strong_model"
COST = {FAST: 1, STRONG: 10}
# (task, difficulty). The labels are the experiment's ground truth.
TASKS = [
    ("12 + 30", "easy"),
    ("17 * 6", "easy"),
    ("(48 - 6) * (9 + 4)", "hard"),
    ("2 ** 10 - 3 * 7", "hard"),
    ("99 * 99", "hard"),
]


def call_model(model, task, difficulty):
    """Assumption: FAST is right on easy tasks only, STRONG on all."""
    correct = calculator(task)
    if model == FAST and difficulty == "hard":
        return correct + 1
    return correct


def verify(task, answer):
    return answer == calculator(task)      # an exact, reliable verifier


def choose_model(task):
    """Observable feature: long expressions are predicted to be hard."""
    return FAST if len(task) <= 10 else STRONG


def single_route(pick):
    def strategy(task, difficulty):
        model = pick(task, difficulty)
        return call_model(model, task, difficulty), COST[model]
    return strategy


def cascade(task, difficulty):
    answer, cost = call_model(FAST, task, difficulty), COST[FAST]
    if not verify(task, answer):                  # escalate on failure
        answer = call_model(STRONG, task, difficulty)
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
