"""Experiment 36: a reducer-backed LangGraph blackboard with provenance."""
from typing import Annotated, TypedDict

from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, START, StateGraph

AUTHORITY = {"catalog_v3": 2, "carrier_api": 2, "cached_page": 1}


def merge_claims(left, right):
    """Reducer: concurrent writes append claims instead of overwriting."""
    merged = {key: list(claims) for key, claims in left.items()}
    for key, claims in right.items():
        merged.setdefault(key, []).extend(claims)
    return merged


class Board(TypedDict):
    claims: Annotated[dict, merge_claims]
    total: int


def claim(key, value, source):
    return {key: [{"value": value, "source": source}]}


def resolve(claims, key):
    return max(claims[key], key=lambda c: AUTHORITY[c["source"]])["value"]


def calculator(state):
    claims = state["claims"]
    total = (resolve(claims, "unit_price") * resolve(claims, "quantity")
             + resolve(claims, "shipping"))
    return {"total": total}


def pricing(state):
    return {"claims": {**claim("unit_price", 80, "catalog_v3"),
                       **claim("quantity", 3, "catalog_v3")}}


def scraper(state):
    return {"claims": claim("unit_price", 90, "cached_page")}


def shipping(state):
    return {"claims": claim("shipping", 15, "carrier_api")}


WRITERS = {"pricing": pricing, "scraper": scraper, "shipping": shipping}


def build(state_type, writers, sink):
    builder = StateGraph(state_type)
    for name, writer in writers.items():
        builder.add_node(name, writer)
        builder.add_edge(START, name)
    builder.add_node("sink", sink)
    builder.add_edge(list(writers), "sink")  # readiness: all writers done
    builder.add_edge("sink", END)
    return builder.compile()


class PlainBoard(TypedDict):
    unit_price: int  # no reducer: one writer per step at most


def without_reducer():
    writers = {"pricing": lambda s: {"unit_price": 80},
               "scraper": lambda s: {"unit_price": 90}}
    try:
        build(PlainBoard, writers, lambda s: {}).invoke({})
    except InvalidUpdateError:
        return "InvalidUpdateError: concurrent writes to unit_price"
    return "no error"


def run():
    state = build(Board, WRITERS, calculator).invoke({"claims": {}})
    prices = sorted(c["value"] for c in state["claims"]["unit_price"])
    return {"unit_price_claims": prices, "total": state["total"],
            "without_reducer": without_reducer()}


if __name__ == "__main__":
    print(run())
