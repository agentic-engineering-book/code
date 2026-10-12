"""Experiment 31: a bounded LangGraph child agent exposed as a tool."""
from typing import Optional, TypedDict

from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from agentic import calculator

calculate = tool(calculator)


class ChildState(TypedDict):
    question: str
    searches: int
    answer: Optional[str]


def build_child(sources):
    def search(state):
        return {"searches": state["searches"] + 1,
                "answer": sources.get(state["question"])}

    def route(state):
        return END if state["answer"] is not None else "search"

    builder = StateGraph(ChildState)
    builder.add_node("search", search)
    builder.add_edge(START, "search")
    builder.add_conditional_edges("search", route, ["search", END])
    return builder.compile()


def make_researcher(sources, max_steps):
    child = build_child(sources)

    @tool
    def researcher(question: str) -> dict:
        """Delegate a research question to a bounded child agent."""
        start = {"question": question, "searches": 0, "answer": None}
        try:
            # The parent's budget crosses the boundary as a recursion limit.
            out = child.invoke(start, {"recursion_limit": max_steps})
        except GraphRecursionError:
            return {"status": "incomplete", "answer": None,
                    "reason": f"step budget {max_steps} exhausted"}
        return {"status": "complete", "answer": out["answer"],
                "steps_used": out["searches"]}

    return researcher


def parent(researcher):
    found = researcher.invoke({"question": "X"})
    if found["status"] != "complete":
        return {"answer": None, "escalate": found}
    value = calculate.invoke({"expression": f"{found['answer']} * 1.10"})
    return {"answer": value, "child": found}


def run():
    return {"cooperative": parent(make_researcher({"X": "80"}, 5)),
            "looping": parent(make_researcher({}, 5))}


if __name__ == "__main__":
    print(run())
