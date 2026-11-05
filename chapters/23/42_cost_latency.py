"""Experiment 42 (Chapter 23): Cost and latency."""
import asyncio
import time

from agentic.live import OpenAIModel

# Three branches of very different length.
BRANCHES = {"A": "Name one primary colour. One word.",
            "B": "Explain in about 150 words how a refrigerator works.",
            "C": "Explain in about 40 words what a compiler does."}


def call(question):
    """One real model call: (milliseconds, tokens)."""
    model = OpenAIModel()
    start = time.perf_counter()
    model.generate([{"role": "user", "content": question}])
    used = model.calls[-1]
    milliseconds = round((time.perf_counter() - start) * 1000)
    return milliseconds, used["input_tokens"] + used["output_tokens"]


# Run the branches one after another. Child spans record exclusive tokens;
# the root span records the inclusive total, as many tracers do.
children = {name: call(question) for name, question in BRANCHES.items()}
root_ms = sum(ms for ms, tokens in children.values())
root_tokens = sum(tokens for ms, tokens in children.values())
print("span breakdown (sequential):")
print(f"  agent.run   {root_ms:>5} ms {root_tokens:>4} tokens (inclusive)")
for name, (ms, tokens) in children.items():
    print(f"    branch {name}  {ms:>5} ms {tokens:>4} tokens")
print(f"naive sum of every span:   {2 * root_tokens} tokens (double-counted)")
print(f"sum of exclusive children: {root_tokens} tokens")


async def parallel():
    start = time.perf_counter()
    results = await asyncio.gather(
        *(asyncio.to_thread(call, q) for q in BRANCHES.values()))
    wall = round((time.perf_counter() - start) * 1000)
    return dict(zip(BRANCHES, results)), wall


branches, wall = asyncio.run(parallel())
critical = max(branches, key=lambda name: branches[name][0])
print("parallel run:", {n: f"{ms} ms" for n, (ms, t) in branches.items()})
print(f"  branch work: {sum(ms for ms, t in branches.values())} ms")
print(f"  wall-clock:  {wall} ms (critical path {critical}: "
      f"{branches[critical][0]} ms)")
