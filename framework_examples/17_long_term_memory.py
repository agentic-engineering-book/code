"""Experiment 17: LangGraph Long-term memory interface. See framework_examples/README.md."""
from langgraph.store.memory import InMemoryStore


def run():
    store = InMemoryStore()
    namespace = ('reader', 'memory')
    store.put(namespace, 'preference', {'text': 'user prefers concise examples'})
    return store.get(namespace, 'preference').value['text']


if __name__ == "__main__":
    print(run())
