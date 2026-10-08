"""Experiment 43: LangChain retry and fallback policy. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    attempts = []
    def flaky(value):
        attempts.append(value)
        if len(attempts) == 1:
            raise ValueError('transient fixture failure')
        return 'success'
    primary = RunnableLambda(flaky).with_retry(
        retry_if_exception_type=(ValueError,), stop_after_attempt=2, wait_exponential_jitter=False)
    fallback = RunnableLambda(lambda x: 'fallback')
    return [primary.with_fallbacks([fallback]).invoke(None), len(attempts)]


if __name__ == "__main__":
    print(run())
