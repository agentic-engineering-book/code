"""Experiment 56 (Chapter 29): Multimodal reasoning."""
import base64
import io
import json

from PIL import Image, ImageDraw, ImageFont

from agentic.live import OpenAIModel

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


def perceive(photo):
    """A real vision model returns structured evidence with confidence."""
    model = OpenAIModel(system="Read the package label. Reply with JSON: "
                        '{"product": ..., "quantity": <integer, or null if '
                        'unreadable>, "confidence": {"product": <0-1>, '
                        '"quantity": <0-1>}}',
                        response_format={"type": "json_object"})
    reply = model.generate([{"role": "user", "content": [
        {"type": "text", "text": "Here is the label photo."},
        {"type": "image_url", "image_url": {"url": photo}}]}])
    return json.loads(reply["answer"])


def naive_fusion(image, order):
    """Deliberate failure: merge the sources, last writer wins."""
    merged = {**order, **{k: v for k, v in image.items()
                          if k != "confidence"}}
    return f"ship {merged['quantity']} x {merged['product']}"


def compare(image, order):
    findings = []
    for field in ("product", "quantity"):
        seen = image.get(field)
        confidence = image["confidence"].get(field, 0.0)
        if seen == order[field]:
            continue
        shown = "UNKNOWN" if seen is None else seen
        findings.append(f"{field}: image says {shown} (confidence "
                        f"{confidence}), order says {order[field]}")
        if seen is None or confidence < MIN_CONFIDENCE:
            findings.append(f"{field}: unreadable or low confidence "
                            "-> re-capture")
    return ("MATCH", []) if not findings else ("ESCALATE", findings)


def show(label, evidence):
    print(f"{label}: {evidence['product']}, quantity {evidence['quantity']}"
          f" (confidence {evidence['confidence']['quantity']})")


image_evidence = perceive(label_photo())
show("image evidence", image_evidence)
print("naive fusion:", naive_fusion(image_evidence, ORDER_RECORD))
decision, findings = compare(image_evidence, ORDER_RECORD)
print("provenance-preserving comparison:", decision)
for finding in findings:
    print("  " + finding)
smudged = perceive(label_photo(smudged=True))
show("smudged label", smudged)
decision, findings = compare(smudged, ORDER_RECORD)
print("comparison:", decision)
for finding in findings:
    print("  " + finding)
