"""Experiment 40: LangChain pairwise judge with an order-swap test."""
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

PROMPT = PromptTemplate.from_template(
    "Rubric: prefer the answer that is correct and grounded in the "
    "evidence.\nEvidence: {evidence}\nFirst: {first}\nSecond: {second}\n"
    'Reply as JSON: {{"winner": "first" | "second"}}')
SHORT = "Revenue was $120m (2025 annual report)."
POLISHED = "Revenue grew strongly to roughly $190m across new markets."


def run():
    # A scripted judge that always picks the first position: a known bias.
    model = FakeListLLM(responses=['{"winner": "first"}'] * 2)
    judge = PROMPT | model | JsonOutputParser()
    evidence = "2025 annual report: revenue $120m"
    order_ab = judge.invoke(
        {"evidence": evidence, "first": SHORT, "second": POLISHED})
    order_ba = judge.invoke(
        {"evidence": evidence, "first": POLISHED, "second": SHORT})
    picked_ab = SHORT if order_ab["winner"] == "first" else POLISHED
    picked_ba = POLISHED if order_ba["winner"] == "first" else SHORT
    return {"order_ab_picks_short": picked_ab == SHORT,
            "order_ba_picks_short": picked_ba == SHORT,
            "position_consistent": picked_ab == picked_ba}


if __name__ == "__main__":
    print(run())
