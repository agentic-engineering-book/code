"""Experiment 44: LangGraph side-effect idempotency boundary. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    sent = set()
    def send(state):
        key = state['value']
        if key in sent:
            return {'value': 'duplicate suppressed'}
        sent.add(key)
        return {'value': 'sent'}
    return [sequence([('send', send)], {'value': 'abc'})['value'] for _ in range(2)]


if __name__ == "__main__":
    print(run())
