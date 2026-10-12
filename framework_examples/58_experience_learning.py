"""Experiment 58: LangGraph store with validated, scoped lessons."""
from langgraph.store.memory import InMemoryStore

EPISODES = [
    ("T41", "API-X 429", "exponential backoff", "recovered"),
    ("T44", "timeout", "retry immediately", "recovered"),
    ("T52", "API-X 429", "exponential backoff", "recovered"),
    ("T60", "timeout", "retry immediately", "failed"),
    ("T61", "timeout", "retry immediately", "failed"),
    ("T87", "API-X 429", "exponential backoff", "recovered"),
]
EPISODES_NS, LESSONS_NS = ("agent", "episodes"), ("agent", "lessons")


def promote(store, min_successes=3, min_rate=0.75):
    """Turn raw episodes into lessons only when the evidence supports it."""
    grouped = {}
    for item in store.search(EPISODES_NS, limit=1000):
        key = (item.value["condition"], item.value["action"])
        grouped.setdefault(key, []).append(item)
    for (condition, action), items in grouped.items():
        wins = [i.key for i in items if i.value["outcome"] == "recovered"]
        if len(wins) >= min_successes and len(wins) / len(items) >= min_rate:
            store.put(LESSONS_NS, f"{condition}|{action}", {
                "scope": condition, "action": action,
                "successes": len(wins), "failures": len(items) - len(wins),
                "source_tasks": sorted(wins)})


def advise(store, condition):
    lessons = store.search(LESSONS_NS, filter={"scope": condition})
    return lessons[0].value["action"] if lessons else None


def run():
    store = InMemoryStore()
    for task, condition, action, outcome in EPISODES:
        store.put(EPISODES_NS, task, {"condition": condition,
                                      "action": action, "outcome": outcome})
    promote(store)
    return {
        "lessons": [i.value for i in store.search(LESSONS_NS)],
        "advice": {c: advise(store, c)
                   for c in ("API-X 429", "timeout", "payment declined")},
    }


if __name__ == "__main__":
    print(run())
