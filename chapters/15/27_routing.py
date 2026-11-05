"""Experiment 27 (Chapter 15): Task routing."""
from agentic.live import OpenAIModel

# Labeled tasks: (request, correct route).
TASKS = [
    ("calculate 17 * 6", "math"),
    ("what is refund policy?", "policy"),
    ("write a short email", "write"),
    ("Calculate 3 + 4", "math"),
    ("is the travel policy current?", "policy"),
    ("Write a reply telling the customer whether they can still return "
     "the jacket they bought 40 days ago.", "policy"),
    ("Write a thank-you note to the team for finishing the release.", "write"),
]
# Cost of sending a task of this kind to the wrong route. A policy question
# answered by the writer risks an unsupported answer, so it costs more.
MISROUTE_COST = {"math": 1, "policy": 5, "write": 1}
PLAIN = ("math (calculations), policy (questions answered from company "
         "policy documents), write (drafting text)")
SHARPER = ("math (calculations), policy (any request whose answer depends "
           "on company policy, even when it asks for drafted text), write "
           "(drafting text that needs no policy)")


def rule_router(task):
    if task.startswith("calculate"):
        return "math"
    if "policy" in task:
        return "policy"
    return "write"


def model_router(routes):
    model = OpenAIModel(system="Route the request to one of: " + routes +
                        ". Reply with the route name only.")

    def route(task):
        reply = model.generate([{"role": "user", "content": task}])
        return reply["answer"].strip().lower()
    return route


def evaluate(name, router):
    correct, cost = 0, 0
    for task, gold in TASKS:
        route = router(task)
        if route == gold:
            correct += 1
        else:
            cost += MISROUTE_COST[gold]
            print(f"  {task[:44]!r} -> {route} (should be {gold})")
    print(f"{name}: accuracy {correct}/{len(TASKS)}, misroute cost {cost}")


evaluate("rules", rule_router)
evaluate("model, plain routes", model_router(PLAIN))
evaluate("model, sharper routes", model_router(SHARPER))
