"""Experiment 10 (Chapter 5): Tool failure."""


def weather(city):
    raise TimeoutError("weather service unavailable")


def hidden_call(tool, arguments):
    """BREAK: every failure becomes None, so its cause is lost."""
    try:
        return tool(**arguments)
    except Exception:
        return None


def structured_call(tool, arguments):
    """FIX: a failure becomes an observation the next decision can use."""
    try:
        return {"ok": True, "value": tool(**arguments)}
    except TimeoutError as error:
        return {"ok": False, "error": "timeout",
                "retryable": True, "message": str(error)}
    except (TypeError, ValueError) as error:
        return {"ok": False, "error": "invalid_arguments",
                "retryable": False, "message": str(error)}


decision = {
    "action": "weather",
    "arguments": {"city": "Pretoria"}
}

print("HIDDEN:", hidden_call(weather, decision["arguments"]))
print("STRUCTURED:")
result = structured_call(weather, decision["arguments"])
for key, value in result.items():
    print(f"  {key}: {value}")
