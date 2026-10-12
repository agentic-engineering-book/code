"""Experiment 42 (Chapter 23): Cost and latency."""
# Fixture spans: (span_id, parent_id, name, start_ms, end_ms, cost).
# The root's cost is inclusive (it already contains its children's cost);
# every other cost is exclusive to its own span.
SPANS = [
    ("S1", None, "agent.run", 0, 1600, 0.010),
    ("S2", "S1", "retrieve", 0, 300, 0.001),
    ("S3", "S1", "model", 300, 1100, 0.004),
    ("S4", "S1", "calculator", 1100, 1110, 0.000),
    ("S5", "S1", "model", 1110, 1600, 0.005),
]
# Three research branches that run in parallel after "start".
BRANCHES = {"A": 200, "B": 900, "C": 400}


def duration(span):
    return span[4] - span[3]


print("span breakdown:")
for span in SPANS:
    indent = "" if span[1] is None else "  "
    print(f"  {indent + span[2]:<13} {duration(span) / 1000:.2f} s "
          f"${span[5]:.3f}")

naive_cost = sum(span[5] for span in SPANS)
leaf_cost = sum(span[5] for span in SPANS if span[1] is not None)
print(f"naive sum of every span:    ${naive_cost:.3f}  (double-counted)")
print(f"sum of exclusive children:  ${leaf_cost:.3f}")

slowest = max(SPANS[1:], key=duration)
print(f"largest child span: {slowest[2]} ({duration(slowest)} ms)")

work = sum(BRANCHES.values())
critical = max(BRANCHES, key=BRANCHES.get)
print(f"parallel branch work: {work} ms")
print(f"wall-clock (critical path {critical}): {BRANCHES[critical]} ms")
