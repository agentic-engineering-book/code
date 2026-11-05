"""Experiment 57: Prompt revision, LangChain. See framework_examples/README."""
from langchain_core.prompts import ChatPromptTemplate

from framework_examples.support import chat

B, T = "BILLING", "TECHNICAL"
# House rule the first prompt does not state: a payment problem caused by
# a bug in our app is TECHNICAL.
SPLITS = {
    "dev": [("charged twice after the app crashed at checkout", T),
            ("my invoice has the wrong company name", B),
            ("the payment page threw an error and took my money twice", T),
            ("cannot log in after the update", T)],
    "valid.": [("double charge caused by the checkout freezing", T),
               ("refund for the annual plan I cancelled", B),
               ("billed for a seat I removed last month", B),
               ("app crashed mid-payment and I paid twice", T)],
    "test": [("I was charged twice because the app crashed during "
              "checkout", T),
             ("refund for the duplicate payment the checkout bug caused", T),
             ("the invoice shows the wrong VAT number", B),
             ("app froze and billed me for an order that never went "
              "through", T),
             ("please refund last month, I cancelled in time", B),
             ("password reset email never arrives", T),
             ("card was charged although the order failed with error 500",
              T),
             ("why did my price go up this month?", B)],
}
V1 = ("Classify the support request as BILLING or TECHNICAL. "
      "Reply with the label only.")
CLASSIFY = ChatPromptTemplate.from_messages(
    [("system", "{instructions}"), ("user", "{request}")])


def correct(prompt, split):
    """One real model call per row; True where the label is right."""
    chain = CLASSIFY.partial(instructions=prompt) | chat()
    rows = SPLITS[split]
    replies = chain.batch([{"request": r} for r, _ in rows])
    return [reply.text.strip() == gold
            for reply, (_, gold) in zip(replies, rows)]


def run():
    dev = correct(V1, "dev")
    failures = [row for row, ok in zip(SPLITS["dev"], dev) if not ok]
    # A real model revises the prompt from the development failures.
    revised = str(chat().invoke(
        "You improve classification prompts. Reply with the new prompt "
        f"only.\n\nCurrent prompt:\n{V1}\n\nIt got these wrong (request "
        "-> correct label):\n"
        + "\n".join(f"- {r} -> {g}" for r, g in failures)
        + "\n\nWrite an improved prompt that states the general rule, "
        "not these examples.").text)
    prompts = {"v1": V1, "revised": revised,
               # A candidate that simply lists the development examples.
               "examples": V1 + "\nKnown cases:\n" + "\n".join(
                   f"- {r} -> {g}" for r, g in SPLITS["dev"])}
    results = {name: {split: (dev if (name, split) == ("v1", "dev")
                              else correct(prompt, split))
                      for split in SPLITS}
               for name, prompt in prompts.items()}
    lines = [f"v1 failed {len(failures)} of {len(dev)} development cases",
             f"{'prompt':<9}" + "".join(f"{s:>7}" for s in SPLITS)]
    for name, scores in results.items():
        lines.append(f"{name:<9}" + "".join(
            f"{sum(ok)}/{len(ok)}".rjust(7) for ok in scores.values()))
    chosen = max(["revised", "examples"],
                 key=lambda n: sum(results[n]["valid."]))
    test, base = results[chosen]["test"], results["v1"]["test"]
    gain = sum(test) > sum(base)
    no_regression = all(
        sum(ok for ok, (_, g) in zip(test, SPLITS["test"]) if g == label)
        >= sum(ok for ok, (_, g) in zip(base, SPLITS["test"]) if g == label)
        for label in (B, T))
    lines.append(f"chosen on validation: {chosen}")
    lines.append(f"promote: {gain and no_regression} (held-out gain "
                 f"{gain}, no slice regression {no_regression})")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
