"""Experiment 53: LangGraph inspect/edit/check workflow. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop
import ast


def run():
    def test(state):
        tree = ast.parse(state['value'])
        # Inspect a bounded fixture rather than executing arbitrary generated code.
        passed = isinstance(tree.body[0].body[0].value.op, ast.Add)
        return {'step': int(passed)}
    state = sequence([
        ('inspect', lambda s: {'value': 'def add(a,b): return a-b'}),
        ('edit', lambda s: {'value': s['value'].replace('a-b', 'a+b')}),
        ('test', test)], {})
    return {'code': state['value'], 'fixture_check_passed': bool(state['step'])}


if __name__ == "__main__":
    print(run())
