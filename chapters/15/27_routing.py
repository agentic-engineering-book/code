"""Experiment 27 (Chapter 15): Task routing."""
# Labeled tasks: (request, correct route).
TASKS = [
    ("calculate 17 * 6", "math"),
    ("what is refund policy?", "policy"),
    ("write a short email", "write"),
    ("Calculate 3 + 4", "math"),
    ("is the travel policy current?", "policy"),
]
# Cost of sending a task of this kind to the wrong route. A policy question
# answered by the writer risks an unsupported answer, so it costs more.
MISROUTE_COST = {"math": 1, "policy": 5, "write": 1}


def rule_router(task):
    if task.startswith("calculate"):
        return "math"
    if "policy" in task:
        return "policy"
    return "write"


def misroute(task):
    """BREAK: every task goes to the writing workflow."""
    return "write"


# Stand-in for a semantic (model) router: scripted predictions.
SEMANTIC = {"calculate 17 * 6": "math", "what is refund policy?": "write",
            "write a short email": "write", "Calculate 3 + 4": "math",
            "is the travel policy current?": "policy"}


def evaluate(name, router):
    correct, cost = 0, 0
    for task, gold in TASKS:
        route = router(task)
        if route == gold:
            correct += 1
        else:
            cost += MISROUTE_COST[gold]
            print(f"  {name}: {task!r} -> {route} (should be {gold})")
    print(f"{name}: accuracy {correct}/{len(TASKS)}, misroute cost {cost}")


evaluate("rules", rule_router)
evaluate("always-write", misroute)
evaluate("semantic", SEMANTIC.get)
