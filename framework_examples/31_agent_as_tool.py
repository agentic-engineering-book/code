"""Experiment 31: Agent as tool in LangGraph. See framework_examples/README."""
import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator
from framework_examples.support import chat

GOAL = "Find the reported value of X, then calculate X * 1.10."
CHILD_STEPS = 5  # the child's budget of model calls


def agent(tools, counter):
    """A model/tool loop like Experiment 22; counter tallies model calls."""
    model = chat().bind_tools(tools)

    def call_model(state):
        counter["model_calls"] += 1
        return {"messages": [model.invoke(state["messages"])]}
    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    return builder.compile()


def make_researcher(sources, hidden):
    """The child agent, exposed to the parent as one tool."""
    @tool
    def search(query: str) -> str:
        """Search the company reports."""
        hidden["searches"] += 1
        return sources()

    child = agent([search], hidden)

    @tool
    def researcher(question: str) -> str:
        """A research agent that finds facts in the company reports."""
        messages = [SystemMessage("You are a research agent. Use search to "
                                  "answer the question. Reply with the "
                                  "answer only."), HumanMessage(question)]
        start = hidden["model_calls"]
        try:
            # The step budget crosses the boundary as a recursion limit.
            out = child.invoke({"messages": messages},
                               {"recursion_limit": 2 * CHILD_STEPS})
            answer, status = out["messages"][-1].content, "complete"
        except GraphRecursionError:
            answer, status = None, "incomplete"
        return json.dumps({"status": status, "answer": answer,
                           "steps_used": hidden["model_calls"] - start},
                          ensure_ascii=False)
    return researcher


def chain():
    """Every report points to the next one; none contains the value."""
    count = iter(range(1, 100))
    return lambda: (f"Report R{(n := next(count))}: X is not given here; "
                    f"its value is reported in report R{n + 1}.")


SCENARIOS = {
    "source has the value":
        lambda: "Q3 report: the reported value of X is 80.",
    "source has nothing": lambda: "no result",
    "each report points to the next": chain(),
}


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '80 * 1.10'."""
    return safe_calculator(expression)


def short(text, width):
    text = str(text).replace("\u2019", "'").replace("\u00d7", "*")
    text = " ".join(text.replace("**", "").split())
    return text if len(text) <= width else text[:width - 4] + " ..."


def run():
    lines = []
    for label, sources in SCENARIOS.items():
        hidden = {"model_calls": 0, "searches": 0}
        parent = agent([make_researcher(sources, hidden), calculator],
                       {"model_calls": 0})
        start = {"messages": [HumanMessage(GOAL)]}
        try:  # stream keeps the last state if the parent's budget runs out
            for state in parent.stream(start, {"recursion_limit": 6},
                                       stream_mode="values"):
                answer = state["messages"][-1].content
        except GraphRecursionError:
            answer = "(parent step budget exhausted)"
        messages = state["messages"]
        actions = [call["name"] for m in messages
                   for call in getattr(m, "tool_calls", [])]
        returned = [m.content for m in messages if m.type == "tool"
                    and m.name == "researcher"]
        lines.append(label)
        lines.append("  researcher returned: " + short(returned[0], 50))
        lines.append(f"  parent actions: {actions}")
        lines.append(f"  hidden child work: model calls="
                     f"{hidden['model_calls']}, searches={hidden['searches']}")
        lines.append("  answer: " + short(answer, 64))
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
