"""Experiment 44: Idempotency in LangGraph. See framework_examples/README."""
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from framework_examples.support import chat

TURNS = ["Charge the customer 100 dollars for order 42.", "Please try again."]


class PaymentServer:
    """Processes payments; the response to the first call is lost."""

    def __init__(self):
        self.charges = []
        self.results = {}  # idempotency key -> (request, result)
        self.drop_next_response = True

    def send_payment(self, amount, idempotency_key=None):
        request = {"amount": amount}
        if idempotency_key in self.results:
            stored_request, result = self.results[idempotency_key]
            if stored_request != request:
                raise ValueError("idempotency key reused for a new request")
            return result
        self.charges.append(amount)
        result = f"charge-{len(self.charges)}"
        if idempotency_key is not None:
            self.results[idempotency_key] = (request, result)
        if self.drop_next_response:
            self.drop_next_response = False
            raise TimeoutError("response lost after the charge")
        return result


def conversation(server, idempotency_key=None):
    """A real agent; the user asks for the charge, then asks it to retry."""
    @tool
    def send_payment(amount: int) -> str:
        """Charge the customer's card; amount in dollars."""
        try:
            return server.send_payment(amount, idempotency_key)
        except TimeoutError:
            return "error: TimeoutError: no response from the payment service"

    model = chat().bind_tools([send_payment])
    builder = StateGraph(MessagesState)
    builder.add_node(
        "model", lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([send_payment]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "order-42"},
              "recursion_limit": 8}
    return [graph.invoke({"messages": [HumanMessage(content=turn)]},
                         config)["messages"][-1].content for turn in TURNS]


def run():
    lines = []
    for label, key in [("no key", None), ("with key", "order-42-payment")]:
        server = PaymentServer()
        replies = conversation(server, key)
        lines += [f"{label}: charges {server.charges}",
                  "  agent after the timeout: "
                  + " ".join(replies[0].split())[:44] + "..."]
    try:
        server.send_payment(250, idempotency_key="order-42-payment")
    except ValueError as error:
        lines += ["key reused with a different amount:", f"  {error}"]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
