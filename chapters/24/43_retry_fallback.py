"""Experiment 43 (Chapter 24): Retry, backoff, fallback."""
import random

RETRYABLE = (TimeoutError, ConnectionError)
MAX_ATTEMPTS = 3
BASE_DELAY = 0.1
jitter = random.Random(42)  # seeded so every run prints the same delays


def make_flaky(failures):
    calls = {"count": 0}

    def flaky_tool():
        calls["count"] += 1
        if calls["count"] <= failures:
            raise TimeoutError("upstream timeout")
        return "success"
    return flaky_tool


def divide_by_zero():
    raise ValueError("invalid input: division by zero")


def call_with_retry(tool, fallback=None):
    delays = []
    for attempt in range(MAX_ATTEMPTS):
        try:
            return tool(), attempt + 1, delays
        except RETRYABLE:
            if attempt + 1 < MAX_ATTEMPTS:
                delay = BASE_DELAY * 2 ** attempt + jitter.uniform(0, 0.05)
                delays.append(round(delay, 3))  # a real client sleeps here
        except ValueError as error:  # permanent: retrying cannot help
            return f"stopped: {error}", attempt + 1, delays
    if fallback is None:
        raise RuntimeError(f"gave up after {MAX_ATTEMPTS} attempts")
    return fallback(), MAX_ATTEMPTS, delays


print("fails twice:", call_with_retry(make_flaky(2)))
print("permanent:  ", call_with_retry(divide_by_zero))
print("outage:     ", call_with_retry(make_flaky(5), lambda: "fallback"))
try:
    call_with_retry(make_flaky(5))
except RuntimeError as error:
    print("no fallback:", error)
