"""Experiment 26: LangGraph parallel candidate expansion and selection. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    candidates = parallel({'A': lambda: .5, 'B': lambda: .9, 'C': lambda: .4})
    return max(candidates, key=lambda x: x[1])[0]


if __name__ == "__main__":
    print(run())
