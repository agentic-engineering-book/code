"""Experiment 16: LangGraph thread-scoped working memory. See framework_examples/README.md."""
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage


def run():
    builder = StateGraph(MessagesState)
    builder.add_node('respond', lambda s: {'messages': [AIMessage(content='tool result: 42')]})
    builder.add_edge(START, 'respond'); builder.add_edge('respond', END)
    app = builder.compile(checkpointer=InMemorySaver())
    config = {'configurable': {'thread_id': 'working-memory'}}
    app.invoke({'messages': [HumanMessage(content='calculate')]}, config)
    return app.get_state(config).values['messages'][-1].content


if __name__ == "__main__":
    print(run())
