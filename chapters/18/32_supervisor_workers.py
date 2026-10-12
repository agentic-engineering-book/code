"""Experiment 32 (Chapter 18): Supervisor and workers."""
EVIDENCE = {"A": "price 80, rating 4.1", "B": "price 95, rating 4.6"}


def researcher(state):
    return {"evidence": [f"{k}: {v}" for k, v in EVIDENCE.items()]}


def analyst(state):
    if not state["evidence"]:
        return {"findings": []}
    return {"findings": ["A is cheaper", "B is rated higher"]}


def writer(state):
    if not state["findings"]:
        return {"draft": "A and B are broadly comparable."}  # unsupported
    return {"draft": "Comparison: " + "; ".join(state["findings"]) + "."}


WORKERS = {"researcher": researcher, "analyst": analyst, "writer": writer}
NEEDS = {"researcher": [], "analyst": ["evidence"], "writer": ["findings"]}


def supervise(plan, respect_dependencies):
    state = {"evidence": [], "findings": [], "draft": None}
    pending, order = list(plan), []
    while pending:
        if respect_dependencies:
            ready = [w for w in pending if all(state[k] for k in NEEDS[w])]
            if not ready:
                return order, "blocked: no worker has its inputs"
            worker = ready[0]
        else:
            worker = pending[0]
        pending.remove(worker)
        order.append(worker)
        state.update(WORKERS[worker](state))
    return order, state["draft"]


GOOD_PLAN = ["researcher", "analyst", "writer"]
BAD_PLAN = ["writer", "researcher", "analyst"]

for label, plan, respect in [
    ("good decomposition", GOOD_PLAN, False),
    ("bad decomposition", BAD_PLAN, False),
    ("bad decomposition, dependency-aware supervisor", BAD_PLAN, True),
]:
    order, draft = supervise(plan, respect)
    print(f"{label}:")
    print(f"  order: {' -> '.join(order)}")
    print(f"  draft: {draft}")
