"""Experiment 58 (Chapter 30): Experience learning."""
from agentic.live import OpenAIModel, schema

# condition -> action -> outcome, one record per past task
EPISODES = [
    ("T41", "API-X 429", "exponential backoff", "recovered"),
    ("T44", "timeout", "retry immediately", "recovered"),
    ("T52", "API-X 429", "exponential backoff", "recovered"),
    ("T60", "timeout", "retry immediately", "failed"),
    ("T61", "timeout", "retry immediately", "failed"),
    ("T87", "API-X 429", "exponential backoff", "recovered"),
]
NEW_TASKS = {"API-X 429": "The call to API-X returned 429 Too Many Requests.",
             "timeout": "The call to the inventory API timed out.",
             "payment declined": "The customer's card was declined "
                                 "(insufficient funds)."}
ACTIONS = [schema("retry_now", "Retry the failed operation immediately."),
           schema("backoff_retry", "Retry after an exponential backoff."),
           schema("ask_customer", "Ask the customer to act.",
                  message="message")]


def agent_action(lessons, task):
    """A real agent handles a new task with the lessons in its context."""
    model = OpenAIModel(tools=ACTIONS, tool_choice="required",
                        system="Lessons from past tasks:\n- " +
                        "\n- ".join(lessons))
    decision = model.generate([{"role": "user",
                                "content": NEW_TASKS[task] + " Handle it."}])
    return decision["action"]


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
print("validated lessons (evidence, provenance, scope):")
promoted = validated_learning(EPISODES)
validated = [f"{r['scope']} -> {r['action']} ({r['successes']}/"
             f"{r['successes'] + r['failures']} recovered: "
             f"{', '.join(r['source_tasks'])})" for r in promoted]
print("a real agent acts on new tasks:")
for task in NEW_TASKS:
    print(f"  {task:<16} naive -> {agent_action(naive, task):<13} "
          f"validated -> {agent_action(validated, task)}")
