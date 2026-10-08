"""Experiment 18: LangGraph Procedural memory interface. See framework_examples/README.md."""
from langgraph.store.memory import InMemoryStore


def run():
    store = InMemoryStore()
    namespace = ('reader', 'memory')
    store.put(namespace, 'divide', {'text': 'check denominator before division'})
    return store.get(namespace, 'divide').value['text']


if __name__ == "__main__":
    print(run())
