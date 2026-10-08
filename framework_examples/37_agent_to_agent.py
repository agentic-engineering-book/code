"""Experiment 37: LangGraph agent-task lifecycle orchestration. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    task = {'from': 'planner', 'to': 'worker', 'task': 'calculate', 'status': 'submitted'}
    return sequence([
        ('accept', lambda s: {'value': {**s['value'], 'status': 'working'}}),
        ('complete', lambda s: {'value': {**s['value'], 'status': 'completed', 'artifact': 42}})],
        {'value': task})['value']


if __name__ == "__main__":
    print(run())
