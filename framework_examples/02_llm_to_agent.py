"""Experiment 2: LangGraph model/tool loop. See framework_examples/README.md."""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition


def run(live=False):
    @tool
    def multiply(a: int, b: int) -> int:
        """Multiply two integers exactly."""
        return a * b
    if live:
        from langchain_openai import ChatOpenAI
        import os
        model = ChatOpenAI(model=os.environ['BOOK_MODEL'], timeout=30, max_retries=1).bind_tools([multiply])
    else:
        model = FakeMessagesListChatModel(responses=[
            AIMessage(content='', tool_calls=[
                {'name': 'multiply', 'args': {'a': 37, 'b': 42}, 'id': 'calc'}]),
            AIMessage(content='37 x 42 = 1554.')])
    builder = StateGraph(MessagesState)
    builder.add_node('model', lambda s: {'messages': [model.invoke(s['messages'])]})
    builder.add_node('tools', ToolNode([multiply]))
    builder.add_edge(START, 'model')
    builder.add_conditional_edges('model', tools_condition, {'tools': 'tools', END: END})
    builder.add_edge('tools', 'model')
    result = builder.compile().invoke({'messages': [HumanMessage(content='37 x 42? Use the multiply tool.')]},
                                      {'recursion_limit': 10})
    return [m.content for m in result['messages'][1:]]


if __name__ == "__main__":
    import sys
    print(run(live="--live" in sys.argv))
