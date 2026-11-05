"""Experiment 27: Task routing in LangGraph. See framework_examples/README."""
from framework_examples.support import branch, chat

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
# A policy question answered by the writer risks an unsupported answer.
MISROUTE_COST = {"math": 1, "policy": 5, "write": 1}
PLAIN = ("math (calculations), policy (questions answered from company "
         "policy documents), write (drafting text)")
SHARPER = ("math (calculations), policy (any request whose answer depends "
           "on company policy, even when it asks for drafted text), write "
           "(drafting text that needs no policy)")
# Destinations only report where the request landed.
DESTINATIONS = {name: (lambda s, n=name: {"value": n})
                for name in MISROUTE_COST}


def rule_router(state):
    task = state["value"]
    if task.startswith("calculate"):
        return "math"
    if "policy" in task:
        return "policy"
    return "write"


def model_router(routes):
    model = chat()
    system = ("Route the request to one of: " + routes +
              ". Reply with the route name only.")

    def route(state):
        reply = model.invoke([("system", system), ("user", state["value"])])
        name = reply.content.strip().lower()
        return name if name in DESTINATIONS else "write"
    return route


def evaluate(name, router, lines):
    correct, cost = 0, 0
    for task, gold in TASKS:
        route = branch(DESTINATIONS, router, task)  # the conditional edge
        if route == gold:
            correct += 1
        else:
            cost += MISROUTE_COST[gold]
            lines.append(f"  {task[:44]!r} -> {route} (should be {gold})")
    lines.append(f"{name}: accuracy {correct}/{len(TASKS)}, "
                 f"misroute cost {cost}")


def run():
    lines = []
    evaluate("rules", rule_router, lines)
    evaluate("model, plain routes", model_router(PLAIN), lines)
    evaluate("model, sharper routes", model_router(SHARPER), lines)
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
