"""Experiment 57 (Chapter 30): Prompt self-improvement."""

PROMPTS = {
    "v1": "Classify the request as:\nBILLING or TECHNICAL.",
    # Two revisions proposed after reviewing the development failures.
    "v2": ("Classify by the user's primary requested resolution.\n"
           "BILLING:\ncharge, invoice, refund, payment\n"
           "TECHNICAL:\nerror, crash, login, log in, setup"),
    "overfit": ("Classify the request.\n"
                "BILLING:\ncharged twice, invoice is wrong\n"
                "TECHNICAL:\napp crashes, cannot log in"),
}
B, T = "BILLING", "TECHNICAL"
DEVELOPMENT = [("charged twice", B), ("app crashes", T),
               ("invoice is wrong", B), ("cannot log in", T)]
VALIDATION = [("refund my payment", B), ("setup fails with an error", T),
              ("charged for two seats", B), ("login loop", T)]
TEST = [("double charge on card", B), ("password reset never arrives", T),
        ("billing address update", B), ("installer crashes", T),
        ("refund not received", B), ("error 500 on export", T),
        ("card declined at checkout", B)]


def keywords(prompt, label):
    lines = prompt.splitlines()
    if f"{label}:" not in lines:
        return []
    return lines[lines.index(f"{label}:") + 1].split(", ")


def classify(prompt, request):
    """Stands in for a model that follows the keyword lists it is given."""
    for label in (B, T):
        if any(word in request for word in keywords(prompt, label)):
            return label
    return B if "bill" in request else T


def score(name, dataset, label=None):
    rows = [(r, gold) for r, gold in dataset if label in (None, gold)]
    correct = sum(classify(PROMPTS[name], r) == gold for r, gold in rows)
    return correct, len(rows)


def show(name, dataset):
    return "{}/{}".format(*score(name, dataset))


print("development set (the failures the revisions were written from):")
for name in PROMPTS:
    print(f"  {name:<8} {show(name, DEVELOPMENT)}")
print("validation set (used to choose between candidates):")
for name in PROMPTS:
    print(f"  {name:<8} {show(name, VALIDATION)}")
chosen = max(["v2", "overfit"], key=lambda n: score(n, VALIDATION)[0])
print(f"  selected: {chosen}")

print("held-out test set (used once, for the promotion decision):")
for name in ("v1", chosen):
    print(f"  {name:<8} {show(name, TEST)}  billing "
          f"{show(name, [r for r in TEST if r[1] == B])}  technical "
          f"{show(name, [r for r in TEST if r[1] == T])}")
gain = score(chosen, TEST)[0] > score("v1", TEST)[0]
no_regression = all(score(chosen, TEST, lab)[0] >= score("v1", TEST, lab)[0]
                    for lab in (B, T))
print(f"promote {chosen}: {gain and no_regression} "
      f"(held-out gain {gain}, no slice regression {no_regression})")
print(f"lineage: version 2 = prompt {chosen}, parent 1 = v1, "
      "rollback target v1")
