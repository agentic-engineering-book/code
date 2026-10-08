"""Experiment 58: LangGraph experience store with a LangChain lesson-selection stage. See framework_examples/README.md."""
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableLambda


def run():
    store = InMemoryStore(); ns = ('agent', 'experience')
    store.put(ns, 'task1', {'outcome': 'success'})
    store.put(ns, 'task2', {'outcome': 'failure'})
    learn = RunnableLambda(lambda items: [item.key for item in items if item.value['outcome'] == 'failure'])
    return learn.invoke(store.search(ns))


if __name__ == "__main__":
    print(run())
