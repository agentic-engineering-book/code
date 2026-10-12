"""Experiment 59: LangChain policy search that exposes reward hacking."""
from langchain_core.runnables import RunnableLambda, RunnableParallel

POLICIES = {"solve_then_close": ["investigate", "fix", "close"],
            "close_immediately": ["close"]}
STEP_COST = 0.1


def episode(actions, hard_constraint=False):
    fixed = closed = False
    for action in actions:
        if action == "close" and hard_constraint and not fixed:
            return None  # the harness makes the action unavailable
        fixed = fixed or action == "fix"
        closed = closed or action == "close"
    return {"fixed": fixed, "closed": closed, "steps": len(actions)}


def proxy(outcome):  # +1 when the ticket is closed
    return int(outcome["closed"]) - STEP_COST * outcome["steps"]


def true_objective(outcome):  # solved, and closing unsolved is harmful
    solved = outcome["closed"] and outcome["fixed"]
    harm = outcome["closed"] and not outcome["fixed"]
    return int(solved) - int(harm) - STEP_COST * outcome["steps"]


def optimize(reward, hard_constraint=False):
    scorer = RunnableParallel({
        name: RunnableLambda(
            lambda _, a=actions: episode(a, hard_constraint))
        for name, actions in POLICIES.items()})
    outcomes = scorer.invoke(None)
    scores = {name: round(reward(o), 2)
              for name, o in outcomes.items() if o is not None}
    return max(scores, key=scores.get), scores


def run():
    return {label: dict(zip(("selected", "scores"), optimize(*args)))
            for label, args in [("proxy", (proxy,)),
                                ("true_objective", (true_objective,)),
                                ("proxy_with_hard_rule", (proxy, True))]}


if __name__ == "__main__":
    print(run())
