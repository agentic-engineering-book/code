"""Experiment 11: LangChain prompt assembly for three refund contexts."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

REQUIRED = {"purchase_age_days", "refund_window_days"}
NOISE = {"customer_tier": "Gold", "preferred_language": "English",
         "last_login": "Tuesday", "shipping_method": "Express",
         "newsletter": "subscribed", "warehouse": "North"}
CONTEXTS = {
    "minimal relevant": {"purchase_age_days": 12, "refund_window_days": 30},
    "relevant + noise": {"purchase_age_days": 12, "refund_window_days": 30,
                         **NOISE},
    "large but incomplete": {"purchase_age_days": 12, **NOISE},
}


def run():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Use only these facts:\n{facts}"),
        ("human", "Can order #17 be refunded?"),
    ])
    render = RunnableLambda(lambda facts: {"facts": "\n".join(
        f"{key}={value}" for key, value in facts.items())})
    chain = render | prompt
    report = {}
    for name, facts in CONTEXTS.items():
        messages = chain.invoke(facts).to_messages()
        report[name] = {
            "prompt_characters": sum(len(m.content) for m in messages),
            "coverage": len(REQUIRED & facts.keys()) / len(REQUIRED),
        }
    return report


if __name__ == "__main__":
    print(run())
