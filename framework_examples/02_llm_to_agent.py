"""Experiment 2: LangGraph model/tool loop."""
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agentic.tools import calculator as evaluate


@tool
def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression."""
    return evaluate(expression)


def build_model(live):
    if live:
        import os
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model=os.environ["BOOK_MODEL"], timeout=30,
                           max_retries=1)
        return model.bind_tools([calculator])
    call = {"name": "calculator", "args": {"expression": "37*42"},
            "id": "call-1"}
    return FakeMessagesListChatModel(responses=[
        AIMessage(content="", tool_calls=[call]),
        AIMessage(content="37 x 42 = 1554.")])


def run(live=False):
    model = build_model(live)
    builder = StateGraph(MessagesState)
    builder.add_node("model",
                     lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")
    question = HumanMessage(content="What is 37 * 42? Use the calculator.")
    result = builder.compile().invoke({"messages": [question]},
                                      {"recursion_limit": 10})
    return [(m.type, m.content) for m in result["messages"][1:]]


if __name__ == "__main__":
    import sys
    print(run(live="--live" in sys.argv))
