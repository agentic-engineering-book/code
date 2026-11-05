"""Experiment 41 (Chapter 23): Tracing."""
import time

from agentic import calculator, execute
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel, schema
from agentic.trace import Tracer

PRICES = {"X": 80}
SCHEMAS = [schema("retrieve", "Look up the price of a product.",
                  key="the product code, such as X"),
           CALCULATOR_SCHEMA]
tracer = Tracer(trace_id="T-1042",
                clock=lambda: round(time.perf_counter() * 1000))  # real ms
model = OpenAIModel(tools=SCHEMAS)


def retrieve(key):
    with tracer.span("vector_search", query=key) as span:
        span["attributes"]["result_count"] = 1
        return PRICES.get(key, "not found")


TOOLS = {"retrieve": retrieve, "calculator": calculator}

with tracer.span("agent.run", goal="price of X plus 10%"):
    messages = [{"role": "user",
                 "content": "Find the price of product X, then add 10%."}]
    for step in range(5):
        with tracer.span("model") as span:
            decision = model.generate(messages)
            call = model.calls[-1]
            span["attributes"]["tokens"] = (call["input_tokens"] +
                                            call["output_tokens"])
        if decision.get("done"):
            break
        with tracer.span(decision["action"], **decision["arguments"]) as span:
            observation = execute(decision, tools=TOOLS)
            span["attributes"]["result"] = observation
        messages += [{"role": "assistant", "content": decision},
                     {"role": "tool", "content": str(observation)}]


def show(parent_id=None, depth=0):
    for span in tracer.children(parent_id):
        duration = span["end"] - span["start"]
        print(f"{'    ' * depth}{span['span_id']} {span['name']} "
              f"{duration} ms {span['status']} {span['attributes']}")
        show(span["span_id"], depth + 1)


print("trace", tracer.trace_id)
show()

print("\nsame spans without parent links:")
for span in sorted(tracer.spans, key=lambda s: s["name"]):
    print(f"  {span['name']:<14} {span['end'] - span['start']:>5} ms")
