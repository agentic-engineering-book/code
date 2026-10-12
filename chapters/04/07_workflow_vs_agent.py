"""Experiment 7 (Chapter 4): Workflow vs agent."""
from agentic.model import PolicyModel
from agentic.tools import execute

DOCUMENTS = {
    "report-en": {"language": "English", "text": "Sales rose 8%."},
    "report-fr": {"language": "French", "text": "Les ventes ont progresse."},
}
TRANSLATIONS = {"Les ventes ont progresse.": "Sales increased."}


def fetch(doc_id):
    return DOCUMENTS[doc_id]


def translate(data):
    return {"language": "English", "text": TRANSLATIONS[data["text"]]}


def format_result(data):
    return "SUMMARY: " + data["text"]


TOOLS = {"fetch": fetch, "translate": translate, "format": format_result}


def workflow(doc_id, trace):
    """The programmer fixed the path; one explicit rule picks the branch."""
    trace.append("fetch")
    data = fetch(doc_id)
    if data["language"] != "English":
        trace.append("translate")
        data = translate(data)
    trace.append("format")
    return format_result(data)


def policy(messages):
    """Stand-in for a model that chooses the next capability at runtime."""
    seen = {m["name"]: m["content"] for m in messages if m["role"] == "tool"}
    if "fetch" not in seen:
        return {"action": "fetch",
                "arguments": {"doc_id": messages[0]["content"]}}
    data = seen.get("translate", seen["fetch"])
    if data["language"] != "English":
        return {"action": "translate", "arguments": {"data": data}}
    if "format" not in seen:
        return {"action": "format", "arguments": {"data": data}}
    return {"done": True, "answer": seen["format"]}


def agent(doc_id, trace, max_steps=6):
    model = PolicyModel(policy)
    messages = [{"role": "user", "content": doc_id}]
    for step in range(max_steps):
        trace.append("model")
        decision = model.generate(messages)
        if decision.get("done"):
            trace.append("done")
            return decision["answer"]
        trace.append(decision["action"])
        observation = execute(decision, tools=TOOLS)
        messages.append({"role": "tool", "name": decision["action"],
                         "content": observation})
    raise RuntimeError("Step limit reached")


for label, doc_id in [("KNOWN PATH", "report-en"),
                      ("OPTIONAL BRANCH", "report-fr")]:
    flow_trace, agent_trace = [], []
    expected = workflow(doc_id, flow_trace)
    answer = agent(doc_id, agent_trace)
    model_calls = agent_trace.count("model")
    tool_calls = len(agent_trace) - model_calls - 1
    print(label)
    print("workflow:", "->".join(flow_trace))
    print("agent:   ", "->".join(agent_trace))
    print(f"same answer: {answer == expected}"
          f" | model calls: 0 vs {model_calls}"
          f" | tool calls: {len(flow_trace)} vs {tool_calls}")
    print()
