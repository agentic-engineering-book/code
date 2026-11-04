"""Experiment 11 (Chapter 6): Context quantity."""
import random

from agentic.live import OpenAIModel

model = OpenAIModel(system="Answer from the facts given. Reply REFUND, "
                           "NO REFUND or CANNOT DECIDE, then one short "
                           "sentence of reason.")

TARGET = "order #17: purchased 33 days ago, refund window 30 days"
INCOMPLETE = "order #17: purchased 33 days ago"  # the window is missing

random.seed(1)  # the same 999 other orders on every run
OTHERS = [f"order #{n}: purchased {random.randint(1, 60)} days ago, "
          f"refund window {random.choice([14, 30, 60])} days"
          for n in range(1000, 1999)]

CONTEXTS = {
    "ORDER 17 ONLY": [TARGET],
    "999 OTHERS, ORDER 17 FIRST": [TARGET] + OTHERS,
    "999 OTHERS, ORDER 17 AT 750": OTHERS[:750] + [TARGET] + OTHERS[750:],
    "999 OTHERS, ORDER 17 LAST": OTHERS + [TARGET],
    "999 OTHERS, WINDOW MISSING": OTHERS[:750] + [INCOMPLETE]
                                  + OTHERS[750:],
}


def verdict(decision):
    """The label the model's reply starts with."""
    for label in ("NO REFUND", "CANNOT DECIDE", "REFUND"):
        if decision["answer"].upper().startswith(label):
            return label
    return "OTHER: " + decision["answer"][:30]


for name, facts in CONTEXTS.items():
    question = ("Facts:\n" + "\n".join(facts) +
                "\n\nCan order #17 be refunded?")
    messages = [{"role": "user", "content": question}]
    answers = [verdict(model.generate(messages)) for trial in range(3)]
    tokens = model.calls[-1]["input_tokens"]
    print(f"{name}  ({tokens:,} input tokens)")
    print("  answers: " + ", ".join(answers))
