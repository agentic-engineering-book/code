"""Experiment 17 (Chapter 8): Episodic and semantic memory."""
from agentic.memory import Memory

ONE_OFF_MARKERS = ("this one", "just this", "for now")


def naive_policy(text):
    return True


def durable_policy(text):
    """Reject requests that announce their own short lifetime."""
    return not any(marker in text.lower() for marker in ONE_OFF_MARKERS)


for name, should_persist in [("NAIVE", naive_policy),
                             ("DURABLE-ONLY", durable_policy)]:
    memory = Memory()
    memory.write("User asked for a Python example of RAG.", "episode")
    memory.write("User prefers concise explanations.", "semantic")

    request = "Use pirate language for this one joke."
    if should_persist(request):
        memory.write(request, "semantic")

    print(f"{name} write policy")
    for kind in ("episode", "semantic"):
        for record in memory.retrieve(kind=kind):
            print(f"  {kind:<9} {record['text']}")
