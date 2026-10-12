"""Experiment 41 (Chapter 23): Tracing."""
from agentic.tools import calculator
from agentic.trace import Tracer

PRICES = {"X": 80}
tracer = Tracer(trace_id="T-1042")
clock = tracer.clock  # a manual clock: work "takes" what we advance


def retrieve(key):
    with tracer.span("vector_search", query=key) as span:
        clock.advance(250)
        span["attributes"]["result_count"] = 3
    return PRICES[key]


def calculate(expression):
    clock.advance(4)
    return round(calculator(expression), 2)


with tracer.span("agent.run", goal="price of X plus 10%"):
    with tracer.span("retrieve", query="X") as span:
        value = retrieve("X")
        span["attributes"]["value"] = value
    expression = f"{value} * 1.10"
    with tracer.span("calculator", expression=expression) as span:
        answer = calculate(expression)
        span["attributes"]["result"] = answer


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
    print(f"  {span['name']:<14} {span['end'] - span['start']:>4} ms")
