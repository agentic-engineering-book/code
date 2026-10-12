"""Live run, Chapter 7: answering from stale and current retrieved evidence."""
from agentic.live import OpenAIModel
from live.common import SMALL_MODEL, arguments, parallel, rate, save, usage

QUESTION = ("When retrieval returns both a superseded and a current policy, "
            "how often does a small model answer with the current value, "
            "with and without effective-date metadata?")
# (question, field, old value, current value)
POLICIES = [
    ("What is the refund window?", "refund window", "30 days", "14 days"),
    ("How long is the warranty?", "warranty", "1 year", "2 years"),
    ("What is the free-shipping threshold?", "free shipping over",
     "$50", "$75"),
    ("How many vacation days do staff get?", "annual leave", "18 days",
     "21 days"),
    ("What is the late-payment fee?", "late fee", "$15", "$25"),
    ("How long is the probation period?", "probation", "6 months",
     "3 months"),
    ("What is the password rotation interval?", "password rotation",
     "90 days", "180 days"),
    ("What is the maximum expense claim without approval?",
     "expense limit", "$200", "$500"),
    ("How long are support tickets kept?", "ticket retention",
     "12 months", "24 months"),
    ("What is the minimum order quantity?", "minimum order", "10 units",
     "25 units"),
]


def context(old, new, field, style):
    old_doc = f"Policy: the {field} is {old}."
    new_doc = f"Policy: the {field} is {new}."
    if style == "no metadata":
        return f"Document 1: {old_doc}\nDocument 2: {new_doc}"
    if style == "metadata":
        return (f"Document 1 (effective 2023-01-01, superseded): {old_doc}\n"
                f"Document 2 (effective 2026-03-01, current): {new_doc}")
    return f"Document 1 (effective 2026-03-01, current): {new_doc}"


def main():
    model_name = arguments(SMALL_MODEL).model
    models = []

    def run(item):
        (question, field, old, new), style, repeat = item
        model = OpenAIModel(model_name, system=(
            "Answer the question using only the documents. One sentence."))
        models.append(model)
        prompt = f"{context(old, new, field, style)}\n\nQuestion: {question}"
        answer = model.generate([{"role": "user", "content": prompt}])["answer"]
        current = new.lower() in answer.lower()
        return {"question": question, "style": style, "repeat": repeat,
                "answer": answer,
                "current_only": current and old.lower() not in answer.lower()}

    styles = ["no metadata", "metadata", "current only"]
    rows = parallel(run, [(p, s, r) for s in styles for p in POLICIES
                          for r in range(2)])
    metrics = [rate(f"Current value only, {style}",
                    [r["current_only"] for r in rows if r["style"] == style])
               for style in styles]
    save("ch07_stale_evidence", 7, QUESTION, [model_name], metrics, rows,
         usage(models))


if __name__ == "__main__":
    main()
