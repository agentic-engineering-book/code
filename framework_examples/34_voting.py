"""Experiment 34: LangGraph parallel voting with explicit aggregation. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop
from collections import Counter


def run():
    votes = parallel({'one': lambda: 'A', 'two': lambda: 'A', 'three': lambda: 'B'})
    return Counter(v for name, v in votes).most_common(1)[0][0]


if __name__ == "__main__":
    print(run())
