"""Experiment 29: Parallelism in LangChain. See framework_examples/README."""
import time

from langchain_core.runnables import RunnableLambda, RunnableParallel

from framework_examples.support import chat

QUESTIONS = {"peru": "What is the capital of Peru? One word.",
             "planet": "What is the largest planet? One word.",
             "gold": "What is the chemical symbol for gold? One word."}
rates = {}


def ask(question):
    return RunnableLambda(lambda _: chat().invoke(question).content.strip())


def get_rate(price):
    time.sleep(1)  # a slow rate service
    rates["EUR"] = 0.8731
    return price


def convert(price):
    rate = rates.get("EUR", "not available")
    reply = chat().invoke(
        f"Convert {price} US dollars to euros. Exchange rate (euros per "
        f"dollar): {rate}. Reply with the amount only.")
    return " ".join(reply.content.split())[:40]


def timed(label, work):
    start = time.perf_counter()
    answers = work()
    return f"{label}: {answers} time={time.perf_counter() - start:.1f} s"


def run():
    asks = {name: ask(question) for name, question in QUESTIONS.items()}
    lines = [timed("sequential",
                   lambda: [a.invoke(None) for a in asks.values()]),
             timed("parallel", lambda: list(
                 RunnableParallel(asks).invoke(None).values()))]
    # Wrong: the conversion runs beside the rate lookup it depends on.
    both = RunnableParallel(rate=RunnableLambda(get_rate),
                            euros=RunnableLambda(convert))
    for trial in range(3):
        rates.clear()
        lines.append(f"dependency parallelized: {both.invoke(100)['euros']}")
    # Right: the dependent step is piped after the lookup.
    rates.clear()
    chain = RunnableLambda(get_rate) | RunnableLambda(convert)
    lines.append(f"dependency respected: {chain.invoke(100)}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
