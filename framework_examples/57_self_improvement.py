"""Experiment 57: LangChain prompt candidates chosen on held-out data."""
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel

INSTRUCTIONS = {
    "v1": "Classify the request as:\nBILLING or TECHNICAL.",
    "v2": ("BILLING:\ncharge, invoice, refund, payment\n"
           "TECHNICAL:\nerror, crash, login, log in, setup"),
    "overfit": ("BILLING:\ncharged twice, invoice is wrong\n"
                "TECHNICAL:\napp crashes, cannot log in"),
}
B, T = "BILLING", "TECHNICAL"
SPLITS = {
    "development": [("charged twice", B), ("app crashes", T),
                    ("invoice is wrong", B), ("cannot log in", T)],
    "validation": [("refund my payment", B), ("setup fails with an error", T),
                   ("charged for two seats", B), ("login loop", T)],
    "test": [("double charge on card", B),
             ("password reset never arrives", T),
             ("billing address update", B), ("installer crashes", T),
             ("refund not received", B), ("error 500 on export", T),
             ("card declined at checkout", B)],
}
TEMPLATE = PromptTemplate.from_template("{instructions}\nRequest: {request}")


def fake_classifier(prompt_value):
    """Stands in for a model that follows the keyword lists it is given."""
    lines = prompt_value.to_string().splitlines()
    request = lines[-1].removeprefix("Request: ")
    for label in (B, T):
        if f"{label}:" in lines:
            words = lines[lines.index(f"{label}:") + 1].split(", ")
            if any(word in request for word in words):
                return label
    return B if "bill" in request else T


def accuracy(name, split):
    chain = (TEMPLATE.partial(instructions=INSTRUCTIONS[name])
             | RunnableLambda(fake_classifier))
    rows = SPLITS[split]
    answers = chain.batch([{"request": r} for r, _ in rows])
    return sum(a == gold for a, (_, gold) in zip(answers, rows))


def run():
    scorer = RunnableParallel({
        name: RunnableLambda(lambda split, n=name: accuracy(n, split))
        for name in INSTRUCTIONS})
    scores = {split: scorer.invoke(split) for split in SPLITS}
    chosen = max(["v2", "overfit"], key=scores["validation"].get)
    promote = scores["test"][chosen] > scores["test"]["v1"]
    return {"scores": scores, "selected_on_validation": chosen,
            "promote": promote}


if __name__ == "__main__":
    print(run())
