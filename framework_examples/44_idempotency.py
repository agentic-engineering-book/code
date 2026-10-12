"""Experiment 44: LangGraph side-effect node guarded by an idempotency key."""
from framework_examples.support import sequence


def run():
    charges = []
    ledger = {}  # idempotency key -> result; production: durable + atomic

    def send_payment(state):
        request = state["value"]
        key = request["idempotency_key"]
        if key in ledger:
            return {"value": ledger[key]}
        charges.append(request["amount"])
        ledger[key] = f"charge-{len(charges)}"
        return {"value": ledger[key]}

    request = {"amount": 100, "idempotency_key": "order-42-payment"}
    first = sequence([("send_payment", send_payment)], {"value": request})
    retry = sequence([("send_payment", send_payment)], {"value": request})
    return {"first": first["value"], "retry": retry["value"],
            "charges": charges}


if __name__ == "__main__":
    print(run())
