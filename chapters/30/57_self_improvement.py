"""Experiment 57 (Chapter 30): Prompt self-improvement."""
from agentic.live import OpenAIModel

B, T = "BILLING", "TECHNICAL"
# House rule the first prompt does not state: a payment problem caused by
# a bug in our app is TECHNICAL.
DEVELOPMENT = [("charged twice after the app crashed at checkout", T),
               ("my invoice has the wrong company name", B),
               ("the payment page threw an error and took my money twice", T),
               ("cannot log in after the update", T)]
VALIDATION = [("double charge caused by the checkout freezing", T),
              ("refund for the annual plan I cancelled", B),
              ("billed for a seat I removed last month", B),
              ("app crashed mid-payment and I paid twice", T)]
TEST = [("I was charged twice because the app crashed during checkout", T),
        ("refund for the duplicate payment the checkout bug caused", T),
        ("the invoice shows the wrong VAT number", B),
        ("app froze and billed me for an order that never went through", T),
        ("please refund last month, I cancelled in time", B),
        ("password reset email never arrives", T),
        ("card was charged although the order failed with error 500", T),
        ("why did my price go up this month?", B)]
V1 = ("Classify the support request as BILLING or TECHNICAL. "
      "Reply with the label only.")


def ask(system, content):
    reply = OpenAIModel(system=system).generate(
        [{"role": "user", "content": content}])
    return reply["answer"].strip()


def score(prompt, dataset, label=None):
    rows = [(r, gold) for r, gold in dataset if label in (None, gold)]
    return sum(ask(prompt, r) == gold for r, gold in rows), len(rows)


failures = [(r, gold) for r, gold in DEVELOPMENT if ask(V1, r) != gold]
PROMPTS = {
    "v1": V1,
    # A real model revises the prompt from the development failures.
    "revised": ask("You improve classification prompts. Reply with the "
                   "new prompt only.",
                   f"Current prompt:\n{V1}\n\nIt got these wrong (request "
                   "-> correct label):\n" +
                   "\n".join(f"- {r} -> {g}" for r, g in failures) +
                   "\n\nWrite an improved prompt that states the general "
                   "rule, not these examples."),
    # A candidate that simply lists the development examples.
    "examples": V1 + "\nKnown cases:\n" +
                "\n".join(f"- {r} -> {g}" for r, g in DEVELOPMENT),
}
print(f"v1 failed {len(failures)} of {len(DEVELOPMENT)} development cases")
print(f"{'prompt':<9} {'dev':>5} {'valid.':>6} {'test':>5}")
results = {name: [score(p, d) for d in (DEVELOPMENT, VALIDATION, TEST)]
           for name, p in PROMPTS.items()}
for name, scores in results.items():
    print(f"{name:<9}" + "".join(f" {c}/{n}".rjust(6) for c, n in scores))
chosen = max(["revised", "examples"], key=lambda n: results[n][1][0])
gain = results[chosen][2][0] > results["v1"][2][0]
no_regression = all(score(PROMPTS[chosen], TEST, lab)[0] >=
                    score(V1, TEST, lab)[0] for lab in (B, T))
print(f"chosen on validation: {chosen}")
print(f"promote: {gain and no_regression} (held-out gain {gain}, "
      f"no slice regression {no_regression})")
