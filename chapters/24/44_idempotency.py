"""Experiment 44 (Chapter 24): Idempotency."""
import textwrap

from agentic.live import OpenAIModel, schema

PAY = schema("send_payment", "Charge the customer's card.",
             amount="amount in dollars")


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
    def send_payment(amount):
        try:
            return server.send_payment(int(amount), idempotency_key)
        except TimeoutError:
            return "error: TimeoutError: no response from the payment service"

    model = OpenAIModel(tools=[PAY])
    messages, replies = [], []
    for turn in ["Charge the customer 100 dollars for order 42.",
                 "Please try again."]:
        messages.append({"role": "user", "content": turn})
        for step in range(4):
            decision = model.generate(messages)
            messages.append({"role": "assistant", "content": decision})
            if decision.get("done"):
                replies.append(decision["answer"])
                break
            messages.append({"role": "tool",
                             "content": send_payment(**decision["arguments"])})
    return replies


for label, key in [("no key", None), ("with key", "order-42-payment")]:
    server = PaymentServer()
    replies = conversation(server, key)
    print(f"{label}: charges {server.charges}")
    print(textwrap.fill(replies[0], 76, initial_indent="  agent after the "
                        "timeout: ", subsequent_indent="    "))

try:
    server.send_payment(250, idempotency_key="order-42-payment")
except ValueError as error:
    print("key reused with a different amount:", error)
