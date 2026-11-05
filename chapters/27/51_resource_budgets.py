"""Experiment 51 (Chapter 27): Resource budgets."""
import textwrap

from agentic.control import Budget
from agentic.live import OpenAIModel, schema

SEARCH_COST = 0.03  # abstract cost units per search, not real prices
SAFETY_NET = 20     # the only limit when no budget is given
SEARCH = schema("search", "Search for sources.", query="search terms")
QUESTION = ("Is it true that drinking coffee doubles productivity? "
            "Find the primary study.")


def search(number):
    """Every search returns another secondary source; none is decisive."""
    return (f"Secondary source {number}: a blog post repeating the claim "
            "without citing the primary study.")


def agent(budget=None):
    """A real research agent; the budget is asked before every search."""
    model = OpenAIModel(tools=[SEARCH], system="Find the primary source "
                        "for the claim before answering.")
    messages, evidence = [{"role": "user", "content": QUESTION}], []
    for step in range(SAFETY_NET):
        decision = model.generate(messages)
        if decision.get("done"):
            return {"status": "COMPLETED", "searches": len(evidence),
                    "answer": decision["answer"]}
        if budget:
            reason = budget.refusal(SEARCH_COST)  # check BEFORE spending
            if reason:
                return {"status": "BUDGET_EXHAUSTED", "reason": reason,
                        "searches": len(evidence), "kept": evidence[-1:]}
            budget.charge(SEARCH_COST)
        evidence.append(search(len(evidence) + 1))
        messages += [{"role": "assistant", "content": decision},
                     {"role": "tool", "content": evidence[-1]}]
    return {"status": "SAFETY_NET", "searches": len(evidence)}


for label, budget in [("no budget", None),
                      ("max 5 steps, max cost 0.10",
                       Budget(max_steps=5, max_cost=0.10)),
                      ("max 2 steps, max cost 1.00",
                       Budget(max_steps=2, max_cost=1.00))]:
    result = agent(budget)
    print(f"{label}: {result['status']} {result.get('reason', '')}")
    print(f"  searches {result['searches']}", end="")
    print(f", cost {budget.cost_used:.2f}" if budget else "")
    if "answer" in result:
        print(textwrap.shorten("  answer: " + result["answer"], 66))
