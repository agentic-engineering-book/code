"""Experiment 10: Tool failure in LangGraph. See framework_examples/README."""
import json
import textwrap

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from framework_examples.support import chat


@tool
def weather(city: str) -> str:
    """Get the current weather in a city."""
    raise TimeoutError("weather service unavailable")


def hidden_call(error: Exception) -> str:
    """BREAK: every failure becomes None, so its cause is lost."""
    return "None"


def structured_call(error: Exception) -> str:
    """FIX: a failure becomes an observation the next decision can use."""
    retryable = isinstance(error, TimeoutError)
    return json.dumps({"ok": False,
                       "error": "timeout" if retryable else "tool_failure",
                       "retryable": retryable, "message": str(error)})


def agent(handler):
    """Model and tool nodes; the error handler shapes the observation."""
    model = chat().bind_tools([weather])
    builder = StateGraph(MessagesState)
    builder.add_node("model",
                     lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([weather], handle_tool_errors=handler))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")
    return builder.compile()


def run():
    lines = []
    question = HumanMessage("What is the weather in Pretoria?")
    for handler in (hidden_call, structured_call):
        state = agent(handler).invoke({"messages": [question]},
                                      {"recursion_limit": 8})
        observation = next(m.content for m in state["messages"]
                           if m.type == "tool")
        answer = " ".join(state["messages"][-1].content.split())
        lines.append(handler.__name__.upper())
        for label, text in [("observation", observation),
                            ("answer", textwrap.shorten(answer, 200))]:
            lines += textwrap.wrap(f"{label}: {text}", 76,
                                   initial_indent="  ",
                                   subsequent_indent="    ")
        lines.append("")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
