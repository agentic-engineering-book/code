"""Experiment 51: Budgets in LangGraph. See framework_examples/README."""
import textwrap

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph

from agentic.control import Budget
from framework_examples.support import chat

SEARCH_COST = 0.03  # abstract cost units per search, not real prices
SAFETY_NET = 20     # the only limit when no budget is given
QUESTION = ("Is it true that drinking coffee doubles productivity? "
            "Find the primary study.")


@tool
def search(query: str) -> str:
    """Search for sources."""


def secondary_source(number):
    """Every search returns another secondary source; none is decisive."""
    return (f"Secondary source {number}: a blog post repeating the claim "
            "without citing the primary study.")


class State(MessagesState):
    status: str
    searches: int


def build(budget):
    model = chat().bind_tools([search])

    def think(state):
        return {"messages": [model.invoke(state["messages"])]}

    def admit(state):  # admission control: asked BEFORE every search
        reason = budget.refusal(SEARCH_COST) if budget else None
        return {"status": f"BUDGET_EXHAUSTED {reason}" if reason
                else "admitted"}

    def act(state):
        if budget:
            budget.charge(SEARCH_COST)
        number = state["searches"] + 1
        results = [ToolMessage(secondary_source(number), tool_call_id=c["id"])
                   for c in state["messages"][-1].tool_calls]
        return {"messages": results, "searches": number}

    builder = StateGraph(State)
    builder.add_node("think", think)
    builder.add_node("admit", admit)
    builder.add_node("act", act)
    builder.add_edge(START, "think")
    builder.add_conditional_edges(
        "think", lambda s: "admit" if s["messages"][-1].tool_calls else END)
    builder.add_conditional_edges(
        "admit", lambda s: "act" if s["status"] == "admitted" else END)
    builder.add_edge("act", "think")
    return builder.compile()


def run():
    lines = []
    for label, budget in [("no budget", None),
                          ("max 5 steps, max cost 0.10",
                           Budget(max_steps=5, max_cost=0.10)),
                          ("max 2 steps, max cost 1.00",
                           Budget(max_steps=2, max_cost=1.00))]:
        final = build(budget).invoke(
            {"messages": [SystemMessage("Find the primary source for the "
                                        "claim before answering."),
                          HumanMessage(QUESTION)],
             "status": "", "searches": 0},
            {"recursion_limit": 3 * SAFETY_NET})
        done = not final["messages"][-1].tool_calls
        lines.append(f"{label}: "
                     + ("COMPLETED" if done else final["status"]))
        cost = f", cost {budget.cost_used:.2f}" if budget else ""
        lines.append(f"  searches {final['searches']}{cost}")
        if done:
            lines.append("  " + textwrap.shorten(
                "answer: " + final["messages"][-1].text, 64))
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
