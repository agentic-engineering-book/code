"""Experiment 42: LangChain invocation cost fixtures and elapsed measurement. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from time import perf_counter


def run():
    started = perf_counter()
    result = RunnableLambda(lambda x: sum(event['cost'] for event in x)).invoke([
        {'cost': .01}, {'cost': .03}])
    return {'fixture_cost': result, 'elapsed_nonnegative': perf_counter() - started >= 0}


if __name__ == "__main__":
    print(run())
