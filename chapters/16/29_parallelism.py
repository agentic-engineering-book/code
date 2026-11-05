"""Experiment 29 (Chapter 16): Parallel execution."""
import asyncio
import time

from agentic.live import OpenAIModel

QUESTIONS = ["What is the capital of Peru? One word.",
             "What is the largest planet? One word.",
             "What is the chemical symbol for gold? One word."]
model = OpenAIModel()
rates = {}


async def ask(question):
    """Run the blocking model call in a thread, so waits can overlap."""
    reply = await asyncio.to_thread(
        model.generate, [{"role": "user", "content": question}])
    return reply["answer"].strip()


async def sequential():
    return [await ask(question) for question in QUESTIONS]


async def concurrent():
    return list(await asyncio.gather(*(ask(q) for q in QUESTIONS)))


async def get_exchange_rate():
    await asyncio.sleep(1)  # a slow rate service
    rates["EUR"] = 0.8731
    return rates["EUR"]


async def convert_price(price):
    rate = rates.get("EUR", "not available")
    return await ask(f"Convert {price} US dollars to euros. Exchange rate "
                     f"(euros per dollar): {rate}. Reply with the amount only.")


async def timed(label, workflow):
    model.calls.clear()
    start = time.perf_counter()
    answers = await workflow()
    seconds = time.perf_counter() - start
    tokens = sum(c["input_tokens"] + c["output_tokens"] for c in model.calls)
    print(f"{label}: {answers} calls={len(model.calls)} tokens={tokens} "
          f"time={seconds:.1f} s")


async def main():
    await timed("sequential", sequential)
    await timed("concurrent", concurrent)
    for trial in range(3):
        rates.clear()
        _, converted = await asyncio.gather(get_exchange_rate(),
                                            convert_price(100))
        print(f"dependency parallelized: {converted}")
    rates.clear()
    await get_exchange_rate()
    print(f"dependency respected: {await convert_price(100)}")


asyncio.run(main())
