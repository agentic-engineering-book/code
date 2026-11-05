"""Experiment 43: Retry, fallback, LangChain. See framework_examples/README."""
import openai
from langchain_core.runnables import RunnableLambda

from framework_examples.support import chat, MODEL, SMALL_MODEL

QUESTION = "What is the capital of Peru? One word."
RETRYABLE = (TimeoutError, openai.APITimeoutError, openai.APIConnectionError,
             openai.RateLimitError)


def model_call(model_name=MODEL, timeouts=0):
    """A real model call; the first `timeouts` attempts are made to fail."""
    attempts = []
    model = chat(model_name)

    def call(question):
        attempts.append(1)
        if len(attempts) <= timeouts:
            raise TimeoutError("injected: upstream timeout")
        return model.invoke(question).content.strip()
    return RunnableLambda(call), attempts


def guarded(runnable, fallback=None):
    """Retry only transient errors, with exponential backoff and jitter."""
    retried = runnable.with_retry(
        retry_if_exception_type=RETRYABLE, stop_after_attempt=3,
        exponential_jitter_params={"initial": 0.1, "max": 1, "jitter": 0.05})
    if fallback is None:
        return retried
    return retried.with_fallbacks([fallback], exceptions_to_handle=RETRYABLE)


def run():
    nano = chat(SMALL_MODEL) | RunnableLambda(lambda m: "fallback: " +
                                              m.content.strip())
    cases = [("fails twice", model_call(timeouts=2), None),
             ("permanent", model_call("no-such-model"), nano),
             ("outage", model_call(timeouts=5), nano),
             ("no fallback", model_call(timeouts=5), None)]
    lines = []
    for label, (runnable, attempts), fallback in cases:
        try:
            result = guarded(runnable, fallback).invoke(QUESTION)
        except Exception as error:  # what reaches the caller
            result = f"stopped: {type(error).__name__}"
        lines.append(f"{label + ':':<13}{result} "
                     f"(attempts: {len(attempts)})")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
