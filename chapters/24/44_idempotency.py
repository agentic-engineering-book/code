"""Experiment 44 (Chapter 24): Idempotency."""


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


def pay_with_one_retry(server, **kwargs):
    try:
        return server.send_payment(100, **kwargs)
    except TimeoutError:
        return server.send_payment(100, **kwargs)  # did the first succeed?


blind = PaymentServer()
result = pay_with_one_retry(blind)
print("no key:   result", result, "| charges", blind.charges)

keyed = PaymentServer()
result = pay_with_one_retry(keyed, idempotency_key="order-42-payment")
print("with key: result", result, "| charges", keyed.charges)

try:
    keyed.send_payment(250, idempotency_key="order-42-payment")
except ValueError as error:
    print("key reused with a different amount:", error)
