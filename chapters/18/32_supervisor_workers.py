"""Experiment 32 (Chapter 18): Supervisor and workers."""
import textwrap

from agentic.live import OpenAIModel

GOAL = "Produce a short evidence-based comparison of products A and B."
EVIDENCE = {"A": "price 80, rating 4.1", "B": "price 95, rating 4.6"}


def ask(system, content):
    reply = OpenAIModel(system=system).generate(
        [{"role": "user", "content": content}])
    return reply["answer"].strip()


def researcher(state):
    return {"evidence": "; ".join(f"{k}: {v}" for k, v in EVIDENCE.items())}


def analyst(state):
    return {"findings": ask(
        "You are the analyst on a team. List the key differences in at most "
        "15 words, using only the evidence.",
        "Evidence: " + (state["evidence"] or "(none yet)"))}


def writer(state):
    return {"draft": ask(
        "You are the writer on a team. Write the final comparison of "
        "products A and B in one sentence, using only the analyst's findings.",
        "Analyst's findings: " + (state["findings"] or "(none yet)"))}


WORKERS = {"researcher": researcher, "analyst": analyst, "writer": writer}
NEEDS = {"researcher": [], "analyst": ["evidence"], "writer": ["findings"]}


def supervise(plan, respect_dependencies):
    state = {"evidence": "", "findings": "", "draft": ""}
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


reply = ask("You are a supervisor with three workers: researcher (gathers "
            "facts), analyst (compares facts), writer (writes the final "
            "text). Reply with the order in which to run them, as names "
            "separated by ' -> '.", "Goal: " + GOAL)
MODEL_PLAN = [name.strip().lower() for name in reply.split("->")]
BAD_PLAN = ["writer", "researcher", "analyst"]  # written by hand

for label, plan, respect in [
    ("model supervisor's plan", MODEL_PLAN, False),
    ("bad plan", BAD_PLAN, False),
    ("bad plan, dependency-aware supervisor", BAD_PLAN, True),
]:
    order, draft = supervise(plan, respect)
    print(f"{label}:")
    print(f"  order: {' -> '.join(order)}")
    print(textwrap.fill(draft, 76, initial_indent="  draft: ",
                        subsequent_indent="         "))
