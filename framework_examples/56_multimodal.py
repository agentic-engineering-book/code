"""Experiment 56: LangChain multimodal message, provenance-keeping fusion."""
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda

ORDER_42 = {"product": "Widget A", "quantity": 7}


def perceive(message):
    """Fixture for a vision model's structured output on the label photo."""
    kinds = [block["type"] for block in message.content_blocks]
    if kinds != ["text", "image"]:
        raise ValueError(f"expected a text and an image block, got {kinds}")
    return {"product": ("Widget A", 0.98), "quantity": (4, 0.62)}


def compare(evidence, threshold=0.9):
    conflicts = []
    for field, recorded in ORDER_42.items():
        seen, confidence = evidence.get(field, ("UNKNOWN", 0.0))
        if seen != recorded:
            conflicts.append({"field": field,
                              "image:label_photo": seen,
                              "confidence": confidence,
                              "database:order_42": recorded,
                              "next": "re-capture" if confidence < threshold
                              else "ask a human"})
    return {"decision": "ESCALATE" if conflicts else "MATCH",
            "conflicts": conflicts}


def run():
    message = HumanMessage(content=[
        {"type": "text", "text": "Does this label match order 42?"},
        {"type": "image", "url": "https://example.invalid/label.png"},
    ])
    chain = RunnableLambda(perceive) | RunnableLambda(compare)
    return chain.invoke(message)


if __name__ == "__main__":
    print(run())
