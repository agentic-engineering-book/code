"""Experiment 56 (Chapter 29): Multimodal reasoning."""

# Structured output of a (simulated) perception step over label_photo.
IMAGE_EVIDENCE = {"product": "Widget A", "quantity": 4,
                  "confidence": {"product": 0.98, "quantity": 0.62}}
ORDER_RECORD = {"product": "Widget A", "quantity": 7}  # database:order_42
MIN_CONFIDENCE = 0.9


def naive_fusion(image, order):
    """Deliberate failure: merge the sources, last writer wins."""
    merged = {**order, **{k: v for k, v in image.items()
                          if k != "confidence"}}
    return f"ship {merged['quantity']} x {merged['product']}"


def claims(image, order):
    for field in ("product", "quantity"):
        yield {"field": field, "value": image.get(field, "UNKNOWN"),
               "source": "image:label_photo",
               "confidence": image["confidence"].get(field, 0.0)}
        yield {"field": field, "value": order[field],
               "source": "database:order_42", "confidence": 1.0}


def compare(image, order):
    findings = []
    for field in ("product", "quantity"):
        pair = [c for c in claims(image, order) if c["field"] == field]
        seen, recorded = pair
        if seen["value"] == recorded["value"]:
            continue
        findings.append(f"{field}: image says {seen['value']} "
                        f"(confidence {seen['confidence']}), "
                        f"order says {recorded['value']}")
        if seen["confidence"] < MIN_CONFIDENCE:
            findings.append(f"{field}: low confidence -> re-capture")
    return ("MATCH", []) if not findings else ("ESCALATE", findings)


print("naive fusion:", naive_fusion(IMAGE_EVIDENCE, ORDER_RECORD))
decision, findings = compare(IMAGE_EVIDENCE, ORDER_RECORD)
print("provenance-preserving comparison:", decision)
for finding in findings:
    print("  " + finding)
occluded = {"product": "Widget A", "confidence": {"product": 0.98}}
decision, findings = compare(occluded, ORDER_RECORD)
print("quantity occluded:", decision)
for finding in findings:
    print("  " + finding)
