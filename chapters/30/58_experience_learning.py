"""Experiment 58 (Chapter 30): Experience learning."""

# condition -> action -> outcome, one record per past task
EPISODES = [
    ("T41", "API-X 429", "exponential backoff", "recovered"),
    ("T44", "timeout", "retry immediately", "recovered"),
    ("T52", "API-X 429", "exponential backoff", "recovered"),
    ("T60", "timeout", "retry immediately", "failed"),
    ("T61", "timeout", "retry immediately", "failed"),
    ("T87", "API-X 429", "exponential backoff", "recovered"),
]
NEW_TASKS = ["API-X 429", "timeout", "payment declined"]


def naive_learning(episodes):
    """Deliberate failure: every success becomes a global rule."""
    lessons = []
    for _, _, action, outcome in episodes:
        if outcome == "recovered" and f"Always {action}" not in lessons:
            lessons.append(f"Always {action}")
    return lessons


def validated_learning(episodes, min_successes=3, min_rate=0.75):
    evidence = {}
    for task, condition, action, outcome in episodes:
        record = evidence.setdefault((condition, action), {
            "scope": condition, "action": action, "successes": 0,
            "failures": 0, "source_tasks": []})
        record["successes" if outcome == "recovered" else "failures"] += 1
        record["source_tasks"].append(task)
    promoted = []
    for record in evidence.values():
        total = record["successes"] + record["failures"]
        rate = record["successes"] / total
        verdict = "promote" if (record["successes"] >= min_successes
                                and rate >= min_rate) else "keep testing"
        print(f"  {record['scope']:<9} -> {record['action']:<19} "
              f"{record['successes']}/{total} {verdict}")
        if verdict == "promote":
            promoted.append(record)
    return promoted


naive = naive_learning(EPISODES)
print("naive lessons:", naive)
for task in NEW_TASKS:
    print(f"  {task:<16} -> {' + '.join(naive)}")
print("validated lessons (evidence, provenance, scope):")
promoted = validated_learning(EPISODES)
print("retrieval for new tasks:")
for task in NEW_TASKS:
    match = [r for r in promoted if r["scope"] == task]
    advice = (f"{match[0]['action']} (from {match[0]['source_tasks']})"
              if match else "no validated lesson; reason from scratch")
    print(f"  {task:<16} -> {advice}")
