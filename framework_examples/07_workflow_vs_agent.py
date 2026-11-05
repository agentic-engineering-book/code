"""Experiment 7: Workflow vs agent. See framework_examples/README."""
import time

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableBranch, RunnableLambda
from langchain_core.tools import tool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from framework_examples.support import chat

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
translator = chat()


@tool
def fetch(doc_id: str) -> dict:
    """Fetch a document by id."""
    return DOCUMENTS[doc_id]


@tool
def translate(text: str) -> str:
    """Translate text into English."""
    return translator.invoke([
        SystemMessage("Translate the user's text into English. "
                      "Reply with the translation only."),
        HumanMessage(text)]).content


@tool("format")
def format_result(text: str) -> str:
    """Format English text as the final summary line."""
    return "SUMMARY: " + text


def step(name, function):
    """A workflow stage that records its name in the trace."""
    def stage(data):
        data["trace"].append(name)
        return function(data)
    return RunnableLambda(stage)


# Workflow: the path is written down; one explicit rule picks the branch.
workflow = (
    step("fetch", lambda d: {**d, **fetch.invoke(d["doc_id"])})
    | RunnableBranch(
        (lambda d: d["language"] != "English",
         step("translate", lambda d: {**d, "text": translate.invoke(
             d["text"])})),
        RunnableLambda(lambda d: d))
    | step("format", lambda d: format_result.invoke(d["text"])))

# Agent: the model node chooses every step at runtime.
TOOLS = [fetch, translate, format_result]
planner = chat().bind_tools(TOOLS, parallel_tool_calls=False)
INSTRUCTION = SystemMessage("Produce the formatted English summary line for "
                            "the document, then reply with that line only.")
builder = StateGraph(MessagesState)
builder.add_node("model", lambda s: {"messages": [
    planner.invoke([INSTRUCTION] + s["messages"])]})
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition)
builder.add_edge("tools", "model")
agent = builder.compile()


class Meter(BaseCallbackHandler):
    """Counts model calls and tokens for every model a run touches."""

    def __init__(self):
        self.calls, self.tokens, self.start = 0, 0, time.perf_counter()

    def on_llm_end(self, response, **kwargs):
        self.calls += 1
        usage = response.generations[0][0].message.usage_metadata
        self.tokens += usage["total_tokens"]

    def __str__(self):
        seconds = time.perf_counter() - self.start
        return (f"model calls: {self.calls}, tokens: {self.tokens}, "
                f"{seconds:.1f} s")


def run_workflow(doc_id):
    meter, trace = Meter(), []
    answer = workflow.invoke({"doc_id": doc_id, "trace": trace},
                             {"callbacks": [meter]})
    return answer, trace, meter


def run_agent(doc_id):
    meter = Meter()
    state = agent.invoke(
        {"messages": [HumanMessage(f"Document id: {doc_id}")]},
        {"callbacks": [meter], "recursion_limit": 14})
    trace = [m.tool_calls[0]["name"] for m in state["messages"]
             if m.type == "ai" and m.tool_calls]
    return state["messages"][-1].content, trace, meter


def run():
    lines = []
    for label, doc_id in [("KNOWN PATH", "report-en"),
                          ("OPTIONAL BRANCH", "report-fr"),
                          ("MISLABELED", "report-es")]:
        lines.append(label)
        for name, runner in [("workflow:", run_workflow),
                             ("agent:   ", run_agent)]:
            answer, trace, meter = runner(doc_id)
            lines.append(f"{name} {' '.join(answer.split())[:66]}")
            lines.append(f"   {'->'.join(trace)} | {meter}")
        lines.append("")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
