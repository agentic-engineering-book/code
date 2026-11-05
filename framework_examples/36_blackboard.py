"""Experiment 36: Blackboard in LangGraph. See framework_examples/README."""
import operator
import re
from typing import Annotated, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph

from framework_examples.support import chat

AUTHORITY = {"catalog_v4": 3, "catalog_v3": 2, "carrier_api": 2,
             "cached_page": 1}
SOURCES = {
    "catalog_v3": "Catalog v3: Widget W2, unit price 80 euros, order "
                  "quantity 3.",
    "carrier_api": "Carrier API: shipping for this order costs 15 euros.",
    "cached_page": "Cached web page: Widget W2 now only 90 euros!",
    "catalog_v4": "Catalog v4 (correction): Widget W2, unit price 90 euros.",
}
WORKERS = {"pricing": ("catalog_v3", ["unit_price", "quantity"]),
           "shipping": ("carrier_api", ["shipping"]),
           "scraper": ("cached_page", ["unit_price"])}


def read(source, key):
    """A real model reads one source and returns the fact it finds."""
    reply = chat().invoke([
        ("system", "Extract facts from the source. Reply with the number "
         "only."),
        ("user", SOURCES[source] + f"\nWhat is the {key.replace('_', ' ')}?")])
    return int(re.findall(r"\d+", reply.content)[0])


def merge_claims(left, right):
    """Reducer: concurrent writes append claims instead of overwriting."""
    merged = {key: list(claims) for key, claims in left.items()}
    for key, claims in right.items():
        merged.setdefault(key, []).extend(claims)
    return merged


class Board(TypedDict, total=False):
    claims: Annotated[dict, merge_claims]
    totals: Annotated[list, operator.add]


def worker(source, keys):
    return lambda state: {"claims": {
        key: [{"value": read(source, key), "source": source}]
        for key in keys}}


def current(claims, key):
    """Resolve conflicting claims by source authority, not by timing."""
    return max(claims[key], key=lambda c: AUTHORITY[c["source"]])["value"]


def calculate(state):
    claims = state["claims"]
    total = (current(claims, "unit_price") * current(claims, "quantity")
             + current(claims, "shipping"))
    return {"totals": [total]}


def build():
    builder = StateGraph(Board)
    for name, (source, keys) in WORKERS.items():
        builder.add_node(name, worker(source, keys))
        builder.add_edge(START, name)
    builder.add_node("calculate", calculate)
    builder.add_edge(list(WORKERS), "calculate")  # readiness: all published
    builder.add_node("correction", worker("catalog_v4", ["unit_price"]))
    builder.add_node("recalculate", calculate)
    builder.add_edge("calculate", "correction")
    builder.add_edge("correction", "recalculate")
    builder.add_edge("recalculate", END)
    return builder.compile()


class PlainBoard(TypedDict, total=False):
    unit_price: int  # no reducer: one writer per step at most


def without_reducer():
    builder = StateGraph(PlainBoard)
    for name in ("pricing", "scraper"):
        source = WORKERS[name][0]
        builder.add_node(name, lambda s, src=source:
                         {"unit_price": read(src, "unit_price")})
        builder.add_edge(START, name)
        builder.add_edge(name, END)
    try:
        builder.compile().invoke({})
    except InvalidUpdateError:
        return "InvalidUpdateError (concurrent writes)"
    return "no error"


def run():
    state = build().invoke({"claims": {}, "totals": []})
    lines = ["unit_price claims kept:"]
    lines += [f"  {claim}" for claim in state["claims"]["unit_price"]]
    lines += [f"total before correction: {state['totals'][0]}",
              f"total after correction: {state['totals'][1]}",
              f"without a reducer: {without_reducer()}"]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
