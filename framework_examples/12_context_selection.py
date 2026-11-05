"""Experiment 12: Context selection. See framework_examples/README."""
import textwrap

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from framework_examples.support import chat

GOOD = [("purchase_age_days=33", 1.0), ("refund_window_days=30", 1.0),
        ("customer_tier=Gold", 0.2), ("newsletter=subscribed", 0.0)]
CORRUPTED = [("purchase_age_days=33", 1.0), ("customer_tier=Gold", 0.9),
             ("refund_window_days=30", 0.1), ("newsletter=subscribed", 0.0)]


def select_top(facts, budget=2):
    """Keep the `budget` highest-scoring facts."""
    ranked = sorted(facts, key=lambda fact: fact[1], reverse=True)
    return {"facts": "\n".join(fact for fact, score in ranked[:budget])}


prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer from the facts given. Reply REFUND, NO REFUND or "
               "CANNOT DECIDE, then one short sentence of reason."),
    ("human", "Facts:\n{facts}\n\nCan order #17 be refunded?"),
])
select = RunnableLambda(select_top)
chain = select | prompt | chat()


def run():
    lines = []
    for label, facts in [("GOOD RANKING", GOOD),
                         ("CORRUPTED RANKING", CORRUPTED)]:
        seen = select.invoke(facts)["facts"].replace("\n", ", ")
        lines.append(f"{label}: the model sees {seen}")
        for reply in chain.batch([facts] * 5):
            lines += textwrap.wrap(" ".join(reply.content.split()), 76,
                                   initial_indent="  ",
                                   subsequent_indent="    ")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
