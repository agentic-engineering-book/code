"""Experiment 17 (Chapter 8): Episodic and semantic memory."""
from agentic.live import OpenAIModel
from agentic.memory import Memory

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
    model = OpenAIModel(system=judge)

    def policy(text):
        reply = model.generate([{"role": "user", "content": text}])
        return "semantic" if "KEEP" in reply["answer"].upper() else "episode"
    return policy


for name, judge in [("NAIVE", None), ("VAGUE JUDGE", VAGUE),
                    ("EXPLICIT JUDGE", EXPLICIT)]:
    policy = write_policy(judge)
    memory = Memory()
    for text in MESSAGES:  # one past conversation
        memory.write(text, policy(text))
    facts = [record["text"] for record in memory.retrieve(kind="semantic",
                                                          limit=10)]
    print(f"{name}, durable memories:")
    for fact in facts:
        print("  " + fact)

    # A week later, a new conversation recalls the durable memories.
    assistant = OpenAIModel(system="What you remember about this user:\n"
                            + "\n".join("- " + fact for fact in facts))
    reply = assistant.generate([{"role": "user",
                                 "content": "What is an embedding?"}])
    print("  NEXT WEEK: " + " ".join(reply["answer"].split())[:62] + "...")
