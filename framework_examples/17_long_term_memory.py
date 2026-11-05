"""Experiment 17: Episodic and semantic memory in a LangGraph store."""
from langgraph.store.memory import InMemoryStore

from framework_examples.support import chat

VAGUE = ("You decide what an assistant should remember about a user "
         "across future conversations. Reply KEEP if the message states a "
         "lasting preference or fact, otherwise DROP. Reply with one word.")
EXPLICIT = VAGUE + (" A request limited to one task or one occasion, such "
                    "as 'this one', 'today' or 'for now', is DROP.")
MESSAGES = [
    "I prefer concise explanations.",
    "Use pirate language for this one joke.",
    "Remember that my project uses Python 3.12.",
    "Answer in French today, I'm practising.",
    "Can you show me a Python example of RAG?",
]


def write_policy(judge):
    """Durable facts become semantic memory; the rest stays an episode."""
    if judge is None:  # the naive policy keeps everything
        return lambda text: "semantic"
    model = chat()

    def policy(text):
        reply = model.invoke([("system", judge), ("human", text)]).content
        return "semantic" if "KEEP" in reply.upper() else "episode"
    return policy


def run():
    lines = []
    for name, judge in [("NAIVE", None), ("VAGUE JUDGE", VAGUE),
                        ("EXPLICIT JUDGE", EXPLICIT)]:
        policy, store = write_policy(judge), InMemoryStore()
        user = ("users", "reader-1")
        for number, text in enumerate(MESSAGES):  # one past conversation
            store.put(user, f"m{number}", {"type": policy(text),
                                           "text": text})
        facts = [item.value["text"] for item in
                 store.search(user, filter={"type": "semantic"})]
        lines.append(f"{name}, durable memories:")
        lines += ["  " + fact for fact in facts]
        # A week later, a new conversation recalls the durable memories.
        system = "What you remember about this user:\n" + "\n".join(
            "- " + fact for fact in facts)
        reply = chat().invoke([("system", system),
                               ("human", "What is an embedding?")])
        lines.append("  NEXT WEEK: " + " ".join(reply.content.split())[:60]
                     + "...")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
