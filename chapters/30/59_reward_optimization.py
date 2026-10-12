"""Experiment 59 (Chapter 30): Reward and reward hacking."""

TICKETS = 10
POLICIES = {  # each policy is the action sequence it takes per ticket
    "solve_then_close": ["investigate", "fix", "close"],
    "close_immediately": ["close"],
}
STEP_COST = 0.1


def run_ticket(actions, hard_constraint):
    state = {"fixed": False, "closed": False, "steps": 0}
    for action in actions:
        if action == "close" and hard_constraint and not state["fixed"]:
            raise PermissionError("close requires a verified fix")
        state["steps"] += 1
        if action == "fix":
            state["fixed"] = True
        if action == "close":
            state["closed"] = True
    return state


def proxy_reward(state):  # "+1 when the ticket is closed"
    return int(state["closed"]) - STEP_COST * state["steps"]


def true_reward(state):  # resolved correctly; closing unsolved is harmful
    solved = state["closed"] and state["fixed"]
    penalty = 1 if state["closed"] and not state["fixed"] else 0
    return int(solved) - penalty - STEP_COST * state["steps"]


def evaluate(reward, hard_constraint=False):
    scores = {}
    for name, actions in POLICIES.items():
        try:
            states = [run_ticket(actions, hard_constraint)
                      for _ in range(TICKETS)]
        except PermissionError:
            continue  # the action is unavailable, not merely penalized
        scores[name] = round(sum(map(reward, states)) / TICKETS, 2)
    return scores


print(f"{'policy':<18} {'proxy':>6} {'true':>6}")
proxy, true = evaluate(proxy_reward), evaluate(true_reward)
for name in POLICIES:
    print(f"{name:<18} {proxy[name]:>6.2f} {true[name]:>6.2f}")
for label, scores in [("proxy reward", proxy), ("true objective", true),
                      ("proxy + hard rule", evaluate(proxy_reward, True))]:
    print(f"optimizing {label:<17} selects {max(scores, key=scores.get)}")
