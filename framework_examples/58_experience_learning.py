"""Experiment 58: Lessons in LangGraph. See framework_examples/README."""
from langchain_core.tools import tool
from langgraph.store.memory import InMemoryStore

from framework_examples.support import chat

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
EPISODES_NS, LESSONS_NS = ("agent", "episodes"), ("agent", "lessons")


@tool
def retry_now() -> str:
    """Retry the failed operation immediately."""


@tool
def backoff_retry() -> str:
    """Retry after an exponential backoff."""


@tool
def ask_customer(message: str) -> str:
    """Ask the customer to act."""


def agent_action(lessons, task):
    """A real agent handles a new task with the lessons in its context."""
    model = chat().bind_tools([retry_now, backoff_retry, ask_customer],
                              tool_choice="required")
    reply = model.invoke([("system", "Lessons from past tasks:\n- "
                           + "\n- ".join(lessons)),
                          ("user", NEW_TASKS[task] + " Handle it.")])
    return reply.tool_calls[0]["name"]


def naive_learning(episodes):
    """Deliberate failure: every success becomes a global rule."""
    return list(dict.fromkeys(f"Always {action}" for *_, action, outcome
                              in episodes if outcome == "recovered"))


def validated_learning(store, lines, min_successes=3, min_rate=0.75):
    """Promote episodes to scoped lessons only with enough evidence."""
    grouped = {}
    for item in store.search(EPISODES_NS, limit=100):
        key = (item.value["condition"], item.value["action"])
        grouped.setdefault(key, []).append(item)
    for (condition, action), items in grouped.items():
        wins = [i.key for i in items if i.value["outcome"] == "recovered"]
        promote = (len(wins) >= min_successes
                   and len(wins) / len(items) >= min_rate)
        verdict = "promote" if promote else "keep testing"
        lines.append(f"  {condition:<9} -> {action:<19} {len(wins)}/"
                     f"{len(items)} {verdict}")
        if promote:  # evidence, provenance and scope travel together
            store.put(LESSONS_NS, f"{condition}|{action}", {
                "text": f"{condition} -> {action} ({len(wins)}/"
                        f"{len(items)} recovered: {', '.join(sorted(wins))})"})
    return [i.value["text"] for i in store.search(LESSONS_NS)]


def run():
    store = InMemoryStore()
    for task, condition, action, outcome in EPISODES:
        store.put(EPISODES_NS, task, {"condition": condition,
                                      "action": action, "outcome": outcome})
    naive = naive_learning(EPISODES)
    lines = [f"naive lessons: {naive}",
             "validated lessons (evidence, provenance, scope):"]
    validated = validated_learning(store, lines)
    lines.append("a real agent acts on new tasks:")
    for task in NEW_TASKS:
        lines.append(f"  {task:<16} naive -> {agent_action(naive, task):<13}"
                     f" validated -> {agent_action(validated, task)}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
