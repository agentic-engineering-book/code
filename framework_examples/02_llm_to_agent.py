"""Experiment 2: Model to agent in LangGraph. See framework_examples/README."""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agentic.tools import calculator as evaluate
from framework_examples.support import chat


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression exactly. Supports + - * / **."""
    return evaluate(expression)


def run():
    model = chat().bind_tools([calculator])
    builder = StateGraph(MessagesState)
    builder.add_node("model",
                     lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")
    question = HumanMessage(content="What is 27611 * 2033?")
    result = builder.compile().invoke({"messages": [question]},
                                      {"recursion_limit": 10})
    lines = []
    for message in result["messages"][1:]:
        if isinstance(message, AIMessage) and message.tool_calls:
            call = message.tool_calls[0]
            lines.append(f"ACTION: {call['name']} {call['args']}")
        elif isinstance(message, ToolMessage):
            lines.append(f"OBSERVATION: {message.content}")
        else:
            lines.append("ANSWER: " + " ".join(message.content.split())[:60])
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
