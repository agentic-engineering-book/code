"""Experiment 46: LangGraph interrupt and explicit human resume. See framework_examples/README.md."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict


def run():
    class State(TypedDict):
        action: str
        executed: bool
    def approve(state):
        approved = interrupt({'action': state['action'], 'question': 'Approve?'})
        return {'executed': approved is True}
    builder = StateGraph(State)
    builder.add_node('approve', approve)
    builder.add_edge(START, 'approve'); builder.add_edge('approve', END)
    app = builder.compile(checkpointer=InMemorySaver())
    config = {'configurable': {'thread_id': 'approval-demo'}}
    paused = app.invoke({'action': 'send_email', 'executed': False}, config)
    result = app.invoke(Command(resume=True), config)
    return {'paused': bool(paused.get('__interrupt__')), 'executed': result['executed']}


if __name__ == "__main__":
    print(run())
