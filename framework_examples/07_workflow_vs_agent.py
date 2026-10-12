"""Experiment 7: LangChain workflow versus LangGraph agent routing."""
from typing import TypedDict

from langchain_core.runnables import RunnableBranch, RunnableLambda
from langgraph.graph import END, START, StateGraph

DOCUMENTS = {
    "report-en": {"language": "English", "text": "Sales rose 8%."},
    "report-fr": {"language": "French", "text": "Les ventes ont progresse."},
}
TRANSLATIONS = {"Les ventes ont progresse.": "Sales increased."}


def fetch(doc_id):
    return dict(DOCUMENTS[doc_id])


def translate(data):
    return {"language": "English", "text": TRANSLATIONS[data["text"]]}


def format_result(data):
    return "SUMMARY: " + data["text"]


# Workflow: the path is written down; one explicit rule picks the branch.
workflow = (RunnableLambda(fetch)
            | RunnableBranch((lambda d: d["language"] != "English",
                              RunnableLambda(translate)),
                             RunnableLambda(lambda d: d))
            | RunnableLambda(format_result))


class AgentState(TypedDict, total=False):
    doc_id: str
    data: dict
    answer: str
    model_calls: int
    next: str


def model(state):
    """Stand-in model: chooses the next node from what it has seen."""
    calls = state.get("model_calls", 0) + 1
    data = state.get("data")
    if data is None:
        choice = "fetch"
    elif data["language"] != "English":
        choice = "translate"
    elif "answer" not in state:
        choice = "format"
    else:
        choice = END
    return {"model_calls": calls, "next": choice}


builder = StateGraph(AgentState)
builder.add_node("model", model)
builder.add_node("fetch", lambda s: {"data": fetch(s["doc_id"])})
builder.add_node("translate", lambda s: {"data": translate(s["data"])})
builder.add_node("format", lambda s: {"answer": format_result(s["data"])})
builder.add_edge(START, "model")
builder.add_conditional_edges("model", lambda s: s["next"])
for node in ("fetch", "translate", "format"):
    builder.add_edge(node, "model")
agent = builder.compile()


def run():
    results = {}
    for doc_id in DOCUMENTS:
        state = agent.invoke({"doc_id": doc_id}, {"recursion_limit": 12})
        same = state["answer"] == workflow.invoke(doc_id)
        results[doc_id] = {"same_answer": same,
                           "agent_model_calls": state["model_calls"]}
    return results


if __name__ == "__main__":
    print(run())
