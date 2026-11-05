"""Experiment 41: Tracing in LangChain. See framework_examples/README."""
import time

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator
from framework_examples.support import chat

GOAL = "Find the price of product X, then add 10%."
vector_search = RunnableLambda(
    lambda key: {"X": 80}.get(key.split()[-1].upper(), "not found"),
    name="vector_search")


@tool
def retrieve(key: str) -> str:
    """Look up the price of a product, such as X."""
    return str(vector_search.invoke(key))


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '80 * 1.1'."""
    return safe_calculator(expression)


class Tracer(BaseCallbackHandler):
    """Keeps model, tool and named spans; graph plumbing runs are skipped,
    so each span's parent is its nearest kept ancestor."""

    KEEP = {"agent.run", "vector_search"}

    def __init__(self):
        self.parent, self.spans = {}, {}

    def _start(self, name, run_id, parent_run_id, keep):
        self.parent[run_id] = parent_run_id
        if keep:
            self.spans[run_id] = {"name": name, "start": time.perf_counter(),
                                  "attributes": {}}

    def _end(self, run_id, **attributes):
        if run_id in self.spans:
            span = self.spans[run_id]
            span["ms"] = round((time.perf_counter() - span["start"]) * 1000)
            span["attributes"].update(attributes)

    def on_chain_start(self, serialized, inputs, *, run_id,
                       parent_run_id=None, **kw):
        name = kw.get("name")
        self._start(name, run_id, parent_run_id, name in self.KEEP)

    def on_chain_end(self, outputs, *, run_id, **kw):
        self._end(run_id)

    def on_chat_model_start(self, serialized, messages, *, run_id,
                            parent_run_id=None, **kw):
        self._start("model", run_id, parent_run_id, True)

    def on_llm_end(self, response, *, run_id, **kw):
        usage = response.generations[0][0].message.usage_metadata
        self._end(run_id, tokens=usage["total_tokens"])

    def on_tool_start(self, serialized, input_str, *, run_id,
                      parent_run_id=None, **kw):
        self._start(serialized["name"], run_id, parent_run_id, True)

    def on_tool_end(self, output, *, run_id, **kw):
        self._end(run_id, result=str(getattr(output, "content", output)))

    def kept_parent(self, run_id):
        parent = self.parent.get(run_id)
        while parent is not None and parent not in self.spans:
            parent = self.parent.get(parent)
        return parent


def run():
    model = chat().bind_tools([retrieve, calculator])
    builder = StateGraph(MessagesState)
    builder.add_node(
        "model", lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([retrieve, calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    tracer = Tracer()
    builder.compile().invoke(
        {"messages": [HumanMessage(content=GOAL)]},
        {"callbacks": [tracer], "run_name": "agent.run",
         "recursion_limit": 10})
    ids = {run_id: f"S{i + 1}" for i, run_id in enumerate(tracer.spans)}
    lines = []

    def show(parent, depth):
        for run_id, span in tracer.spans.items():
            if tracer.kept_parent(run_id) == parent:
                lines.append(f"{'    ' * depth}{ids[run_id]} {span['name']} "
                             f"{span['ms']} ms {span['attributes']}"[:76])
                show(run_id, depth + 1)
    show(None, 0)
    lines.append("same spans without parent links:")
    for span in sorted(tracer.spans.values(), key=lambda s: s["name"]):
        lines.append(f"  {span['name']:<14} {span['ms']:>5} ms")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
