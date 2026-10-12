"""Experiment 17: LangGraph store with typed memories and a write policy."""
from langgraph.store.memory import InMemoryStore

ONE_OFF_MARKERS = ("this one", "just this", "for now")


def write(store, namespace, key, text, kind):
    """Write policy: one-off requests never become durable memory."""
    if kind == "semantic" and any(m in text.lower()
                                  for m in ONE_OFF_MARKERS):
        return False
    store.put(namespace, key, {"type": kind, "text": text})
    return True


def run():
    store = InMemoryStore()
    user = ("users", "reader-1")
    write(store, user, "e1", "User asked for a Python example of RAG.",
          "episode")
    write(store, user, "s1", "User prefers concise explanations.",
          "semantic")
    pirate = write(store, user, "s2",
                   "Use pirate language for this one joke.", "semantic")
    semantic = store.search(user, filter={"type": "semantic"})
    episodes = store.search(user, filter={"type": "episode"})
    return {"pirate_persisted": pirate,
            "semantic": [item.value["text"] for item in semantic],
            "episodes": [item.value["text"] for item in episodes]}


if __name__ == "__main__":
    print(run())
