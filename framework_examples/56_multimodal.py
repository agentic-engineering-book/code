"""Experiment 56: Multimodal in LangChain. See framework_examples/README."""
import base64
import io
from typing import Optional

from langchain_core.messages import HumanMessage
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

from framework_examples.support import chat

ORDER_RECORD = {"product": "Widget A", "quantity": 7}  # database:order_42
MIN_CONFIDENCE = 0.9


def label_photo(smudged=False):
    """Render a package label; optionally smudge the quantity."""
    image = Image.new("RGB", (360, 160), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=28)
    draw.rectangle([5, 5, 354, 154], outline="black", width=3)
    draw.text((20, 25), "Widget A", fill="black", font=font)
    draw.text((20, 85), "Qty: 4", fill="black", font=font)
    if smudged:
        draw.ellipse([75, 70, 175, 135], fill=(60, 60, 60))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(
        buffer.getvalue()).decode()


class Evidence(BaseModel):
    product: str
    quantity: Optional[int]  # None if unreadable
    product_confidence: float  # 0 to 1
    quantity_confidence: float  # 0 to 1


def perceive(photo):
    """A real vision model returns structured evidence with confidence."""
    model = chat().with_structured_output(Evidence)
    evidence = model.invoke([HumanMessage(content=[
        {"type": "text", "text": "Read the package label. Give the "
         "quantity as null if it is unreadable, and your confidence."},
        {"type": "image_url", "image_url": {"url": photo}}])])
    return evidence.model_dump()


def compare(image, order):
    findings = []
    for field in ("product", "quantity"):
        seen, confidence = image[field], image[f"{field}_confidence"]
        if seen == order[field]:
            continue
        shown = "UNKNOWN" if seen is None else seen
        findings.append(f"  {field}: image says {shown} (confidence "
                        f"{confidence}), order says {order[field]}")
        if seen is None or confidence < MIN_CONFIDENCE:
            findings.append(f"  {field}: unreadable or low confidence "
                            "-> re-capture")
    return ["ESCALATE"] + findings if findings else ["MATCH"]


def run():
    lines = []
    for label, smudged in [("clear label", False), ("smudged label", True)]:
        image = perceive(label_photo(smudged))
        lines.append(f"{label}: {image['product']}, quantity "
                     f"{image['quantity']} (confidence "
                     f"{image['quantity_confidence']})")
        merged = {**ORDER_RECORD, **{k: v for k, v in image.items()
                                     if k in ORDER_RECORD}}
        lines.append(f"  naive fusion (last writer wins): ship "
                     f"{merged['quantity']} x {merged['product']}")
        decision, *findings = compare(image, ORDER_RECORD)
        lines.append(f"  provenance-preserving comparison: {decision}")
        lines += findings
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
