"""Experiment 9: LangGraph named-tool dispatch. See framework_examples/README.md."""
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END


def run():
    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b
    @tool
    def maximum(a: int, b: int) -> int:
        """Return the larger integer."""
        return max(a, b)
    decision = AIMessage(content='', tool_calls=[
        {'name': 'maximum', 'args': {'a': 2, 'b': 7}, 'id': 'choice'}])
    builder = StateGraph(MessagesState)
    builder.add_node('tools', ToolNode([add, maximum]))
    builder.add_edge(START, 'tools'); builder.add_edge('tools', END)
    result = builder.compile().invoke({'messages': [decision]})
    return result['messages'][-1].content


if __name__ == "__main__":
    print(run())
