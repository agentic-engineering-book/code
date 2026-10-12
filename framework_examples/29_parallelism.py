"""Experiment 29: LangChain parallel runnables, then a dependent sequence."""
from langchain_core.runnables import RunnableLambda, RunnableParallel


def fetch(name):
    return RunnableLambda(lambda _: f"fact {name}", name=f"fetch_{name}")


def run():
    # Independent reads: one RunnableParallel, bounded by max_concurrency.
    independent = RunnableParallel(a=fetch("A"), b=fetch("B"), c=fetch("C"))
    facts = independent.invoke(None, config={"max_concurrency": 2})

    # Dependent work: the conversion needs the rate, so it is piped after it.
    get_rate = RunnableLambda(lambda price: {"price": price, "rate": 0.9})
    convert = RunnableLambda(lambda d: round(d["price"] * d["rate"], 2))
    converted = (get_rate | convert).invoke(100)
    return {"facts": facts, "converted": converted}


if __name__ == "__main__":
    print(run())
