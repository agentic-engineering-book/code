"""Experiment 43: LangChain retry for transient errors, fallback otherwise."""
from langchain_core.runnables import RunnableLambda


def make_tool(failures, error):
    attempts = []

    def tool(value):
        attempts.append(value)
        if len(attempts) <= failures:
            raise error
        return "success"
    return tool, attempts


def guarded(tool):
    primary = RunnableLambda(tool).with_retry(
        retry_if_exception_type=(TimeoutError, ConnectionError),
        stop_after_attempt=3,
        wait_exponential_jitter=False)  # no sleeping in a test fixture
    return primary.with_fallbacks([RunnableLambda(lambda _: "fallback")])


def run():
    results = {}
    cases = {"transient": (2, TimeoutError("upstream timeout")),
             "permanent": (9, ValueError("division by zero")),
             "outage": (9, TimeoutError("upstream timeout"))}
    for label, (failures, error) in cases.items():
        tool, attempts = make_tool(failures, error)
        results[label] = [guarded(tool).invoke(None), len(attempts)]
    return results


if __name__ == "__main__":
    print(run())
