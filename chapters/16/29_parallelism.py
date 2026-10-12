"""Experiment 29 (Chapter 16): Parallel execution."""
import asyncio

SCALE = 0.01  # real seconds per simulated second, so the demo runs quickly
clock = {"now": 0}  # simulated seconds: deterministic, unlike a wall clock
calls = []
rates = {}


async def call_service(name, seconds):
    calls.append(name)
    start = clock["now"]
    await asyncio.sleep(seconds * SCALE)  # waiting, not computing
    clock["now"] = max(clock["now"], start + seconds)
    return f"fact {name}"


async def fetch_a():
    return await call_service("A", 2)


async def fetch_b():
    return await call_service("B", 2)


async def fetch_c():
    return await call_service("C", 2)


async def sequential():
    a = await fetch_a()
    b = await fetch_b()
    c = await fetch_c()
    return [a, b, c]


async def concurrent():
    return list(await asyncio.gather(fetch_a(), fetch_b(), fetch_c()))


async def get_exchange_rate():
    await asyncio.sleep(1 * SCALE)
    rates["EUR"] = 0.9
    return rates["EUR"]


async def convert_price(price):
    rate = rates.get("EUR")
    if rate is None:
        raise RuntimeError("rate not available yet")
    return round(price * rate, 2)


async def timed(label, workflow):
    calls.clear()
    clock["now"] = 0
    results = await workflow()
    print(f"{label}: {results} calls={len(calls)} time={clock['now']} s")


async def main():
    await timed("sequential", sequential)
    await timed("concurrent", concurrent)

    rates.clear()
    both = await asyncio.gather(get_exchange_rate(), convert_price(100),
                                return_exceptions=True)
    print(f"dependency parallelized: {both[1]!r}")

    rates.clear()
    await get_exchange_rate()
    print(f"dependency respected: {await convert_price(100)}")


asyncio.run(main())
