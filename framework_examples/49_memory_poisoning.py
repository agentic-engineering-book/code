"""Experiment 49: LangGraph memory provenance filter. See framework_examples/README.md."""
from langgraph.store.memory import InMemoryStore


def run():
    store = InMemoryStore(); ns = ('reader', 'facts')
    store.put(ns, 'one', {'value': 'trusted fact', 'trusted': True})
    store.put(ns, 'two', {'value': 'malicious instruction', 'trusted': False})
    return [item.value['value'] for item in store.search(ns) if item.value['trusted']]


if __name__ == "__main__":
    print(run())
