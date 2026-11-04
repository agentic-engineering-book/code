"""Experiment 12 (Chapter 6): Context selection."""
import textwrap

from agentic.context import select_top
from agentic.live import OpenAIModel

model = OpenAIModel(system="Answer from the facts given. Reply REFUND, "
                           "NO REFUND or CANNOT DECIDE, then one short "
                           "sentence of reason.")

good_scores = [
    ("purchase_age_days=33", 1.0),
    ("refund_window_days=30", 1.0),
    ("customer_tier=Gold", 0.2),
    ("newsletter=subscribed", 0.0),
]
corrupted_scores = [
    ("purchase_age_days=33", 1.0),
    ("customer_tier=Gold", 0.9),
    ("refund_window_days=30", 0.1),
    ("newsletter=subscribed", 0.0),
]

for label, facts in [("GOOD RANKING", good_scores),
                     ("CORRUPTED RANKING", corrupted_scores)]:
    selected = [fact for fact, score in select_top(facts, budget=2)]
    question = ("Facts:\n" + "\n".join(selected) +
                "\n\nCan order #17 be refunded?")
    print(f"{label}: the model sees {', '.join(selected)}")
    for trial in range(5):
        answer = model.generate([{"role": "user", "content": question}])
        print(textwrap.fill(answer["answer"], 76, initial_indent="  ",
                            subsequent_indent="    "))
