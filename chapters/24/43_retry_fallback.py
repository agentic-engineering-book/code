"""Experiment 43 (Chapter 24): Retry, backoff, fallback."""
import random
import time

import openai

from agentic.live import OpenAIModel

QUESTION = [{"role": "user", "content": "What is the capital of Peru? "
             "One word."}]
RETRYABLE = (TimeoutError, openai.APITimeoutError, openai.APIConnectionError,
             openai.RateLimitError)
PERMANENT = (openai.NotFoundError, openai.BadRequestError)
MAX_ATTEMPTS = 3
BASE_DELAY = 0.1


def model_call(model_name="gpt-5.4-mini-2026-03-17", timeouts=0):
    """A real model call; the first `timeouts` attempts are made to fail."""
    attempts = {"count": 0}

    def call():
        attempts["count"] += 1
        if attempts["count"] <= timeouts:
            raise TimeoutError("injected: upstream timeout")
        reply = OpenAIModel(model_name).generate(QUESTION)
        return reply["answer"].strip()
    return call


def call_with_retry(call, fallback=None):
    delays = []
    for attempt in range(MAX_ATTEMPTS):
        try:
            return call(), attempt + 1, delays
        except RETRYABLE:
            if attempt + 1 < MAX_ATTEMPTS:
                delay = BASE_DELAY * 2 ** attempt + random.uniform(0, 0.05)
                delays.append(round(delay, 2))
                time.sleep(delay)
        except PERMANENT as error:  # retrying cannot help
            return f"stopped: {type(error).__name__}", attempt + 1, delays
    if fallback is None:
        raise RuntimeError(f"gave up after {MAX_ATTEMPTS} attempts")
    return fallback(), MAX_ATTEMPTS, delays


nano = model_call("gpt-5.4-nano-2026-03-17")
print("fails twice:", call_with_retry(model_call(timeouts=2)))
print("permanent:  ", call_with_retry(model_call("no-such-model")))
print("outage:     ", call_with_retry(model_call(timeouts=5),
                                     lambda: "fallback: " + nano()))
try:
    call_with_retry(model_call(timeouts=5))
except RuntimeError as error:
    print("no fallback:", error)
