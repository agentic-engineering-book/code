"""Experiment 30: LangGraph fan-out, reducer, and barrier join. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    parts = parallel({'A': lambda: 'fact A', 'B': lambda: 'fact B', 'C': lambda: 'fact C'})
    return ' | '.join(value for name, value in parts)


if __name__ == "__main__":
    print(run())
