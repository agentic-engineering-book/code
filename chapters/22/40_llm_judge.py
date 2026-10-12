"""Experiment 40 (Chapter 22): LLM-as-judge."""
RUBRIC = """Score 0-2:
2 = correct, complete, grounded
1 = partially correct
0 = incorrect or unsupported"""

# Trusted labels for a small calibration subset.
LABELED = [
    ("Revenue was $120m (source: 2025 annual report).", 2),
    ("Revenue grew strongly to roughly $190m last year, driven by "
     "expansion into several new regional markets.", 0),
    ("Revenue was $120m.", 1),
    ("I don't know.", 0),
]


def judge(answer, rubric):
    """Stand-in for a model judge with a known bias: it rewards length."""
    return 2 if len(answer) > 60 else 1


def pairwise_judge(first, second):
    """Stand-in for a pairwise judge with a known bias: position."""
    return first


print("calibration against trusted labels:")
false_positives = 0
for answer, label in LABELED:
    score = judge(answer, RUBRIC)
    false_positives += score > label
    print(f"  label={label} judge={score}  {answer[:40]}")
agreement = sum(judge(a, RUBRIC) == label for a, label in LABELED)
print(f"agreement {agreement}/{len(LABELED)}, "
      f"over-scored {false_positives}/{len(LABELED)}")

short, polished = LABELED[0][0], LABELED[1][0]
first_order = pairwise_judge(short, polished) == short
second_order = pairwise_judge(polished, short) == short
print("swap test: prefers short answer in order AB:", first_order,
      "| in order BA:", second_order)
print("position-consistent:", first_order == second_order)
