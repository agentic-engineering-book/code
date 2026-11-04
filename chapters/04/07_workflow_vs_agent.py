"""Experiment 7 (Chapter 4): Workflow vs agent."""
from agentic.live import OpenAIModel, schema
from agentic.tools import execute

DOCUMENTS = {
    "report-en": {"language": "English",
                  "text": "Sales rose 8% in the third quarter."},
    "report-fr": {"language": "French",
                  "text": "Les ventes ont progressé de 8 % au troisième "
                          "trimestre."},
    "report-es": {"language": "English",  # wrong: the text is Spanish
                  "text": "Las ventas subieron un 8 % en el tercer "
                          "trimestre."},
}

translator = OpenAIModel(system="Translate the user's text into English. "
                                "Reply with the translation only.")


def fetch(doc_id):
    return DOCUMENTS[doc_id]


def translate(text):
    return translator.generate([{"role": "user", "content": text}])["answer"]


def format_result(text):
    return "SUMMARY: " + text


TOOLS = {"fetch": fetch, "translate": translate, "format": format_result}


def workflow(doc_id, trace):
    """The programmer fixed the path; one explicit rule picks the branch."""
    trace.append("fetch")
    document = fetch(doc_id)
    text = document["text"]
    if document["language"] != "English":
        trace.append("translate")
        text = translate(text)
    trace.append("format")
    return format_result(text)


planner = OpenAIModel(tools=[
    schema("fetch", "Fetch a document by id.", doc_id="the document id"),
    schema("translate", "Translate text into English.", text="the text"),
    schema("format", "Format English text as the final summary line.",
           text="the English text"),
], system="Produce the formatted English summary line for the document, "
          "then reply with that line only.")


def agent(doc_id, trace, max_steps=6):
    """The model chooses every step at runtime."""
    messages = [{"role": "user", "content": f"Document id: {doc_id}"}]
    for step in range(max_steps):
        decision = planner.generate(messages)
        messages.append({"role": "assistant", "content": decision})
        if decision.get("done"):
            return decision["answer"]
        trace.append(decision["action"])
        observation = execute(decision, tools=TOOLS)
        messages.append({"role": "tool", "content": str(observation)})
    raise RuntimeError("Step limit reached")


def cost(*models):
    """Model calls, tokens and seconds since the counters were cleared."""
    calls = [call for model in models for call in model.calls]
    tokens = sum(c["input_tokens"] + c["output_tokens"] for c in calls)
    seconds = sum(c["seconds"] for c in calls)
    for model in models:
        model.calls.clear()
    return f"model calls: {len(calls)}, tokens: {tokens}, {seconds:.1f} s"


for label, doc_id in [("KNOWN PATH", "report-en"),
                      ("OPTIONAL BRANCH", "report-fr"),
                      ("MISLABELED", "report-es")]:
    print(label)
    trace = []
    print("workflow:", workflow(doc_id, trace))
    print("  ", "->".join(trace), "|", cost(translator))
    trace = []
    print("agent:   ", agent(doc_id, trace))
    print("  ", "->".join(trace), "|", cost(planner, translator))
    print()
