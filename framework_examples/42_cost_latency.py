"""Experiment 42: Cost, latency, LangChain. See framework_examples/README."""
import time

from langchain_core.runnables import RunnableLambda, RunnableParallel

from framework_examples.support import chat

BRANCHES = {"A": "Name one primary colour. One word.",
            "B": "Explain in about 150 words how a refrigerator works.",
            "C": "Explain in about 40 words what a compiler does."}


def timed(question):
    """One real model call as a runnable returning (ms, tokens)."""
    def call(_):
        start = time.perf_counter()
        reply = chat().invoke(question)
        ms = round((time.perf_counter() - start) * 1000)
        return ms, reply.usage_metadata["total_tokens"]
    return RunnableLambda(call)


def run():
    branches = {name: timed(q) for name, q in BRANCHES.items()}
    children = {name: b.invoke(None) for name, b in branches.items()}
    root_ms = sum(ms for ms, _ in children.values())
    root_tokens = sum(tokens for _, tokens in children.values())
    lines = ["span breakdown (sequential):",
             f"  agent.run   {root_ms:>5} ms {root_tokens:>4} tokens "
             "(inclusive)"]
    for name, (ms, tokens) in children.items():
        lines.append(f"    branch {name}  {ms:>5} ms {tokens:>4} tokens")
    lines += [f"naive sum of every span:   {2 * root_tokens} tokens "
              "(double-counted)",
              f"sum of exclusive children: {root_tokens} tokens"]
    start = time.perf_counter()
    parallel = RunnableParallel(branches).invoke(None)
    wall = round((time.perf_counter() - start) * 1000)
    critical = max(parallel, key=lambda name: parallel[name][0])
    lines += ["parallel run: " + ", ".join(
                  f"{n} {ms} ms" for n, (ms, _) in parallel.items()),
              f"  branch work: {sum(ms for ms, _ in parallel.values())} ms",
              f"  wall-clock:  {wall} ms (critical path {critical}: "
              f"{parallel[critical][0]} ms)"]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
