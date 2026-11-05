"""Experiment 11: Context quantity. See framework_examples/README."""
import random

from langchain_core.prompts import ChatPromptTemplate

from framework_examples.support import chat

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

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer from the facts given. Reply REFUND, NO REFUND or "
               "CANNOT DECIDE, then one short sentence of reason."),
    ("human", "Facts:\n{facts}\n\nCan order #17 be refunded?"),
])
chain = prompt | chat()


def verdict(answer):
    """The label the model's reply starts with."""
    for label in ("NO REFUND", "CANNOT DECIDE", "REFUND"):
        if answer.upper().startswith(label):
            return label
    return "OTHER: " + answer[:30]


def run():
    lines = []
    for name, facts in CONTEXTS.items():
        replies = chain.batch([{"facts": "\n".join(facts)}] * 3)
        tokens = replies[-1].usage_metadata["input_tokens"]
        lines.append(f"{name}  ({tokens:,} input tokens)")
        answers = ", ".join(verdict(reply.content) for reply in replies)
        lines.append("  answers: " + answers)
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
