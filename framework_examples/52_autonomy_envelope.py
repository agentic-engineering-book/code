"""Experiment 52: LangGraph enforcement of an explicit autonomy envelope. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    envelope = {'tools': {'search'}, 'max_steps': 20, 'max_cost': 1.0}
    request = {'tool': 'send_email', 'steps': 1, 'cost': .01}
    return branch({'allow': lambda s: {'value': 'allowed'}, 'deny': lambda s: {'value': 'denied'}},
        lambda s: 'allow' if s['value']['tool'] in envelope['tools']
            and s['value']['steps'] < envelope['max_steps']
            and s['value']['cost'] <= envelope['max_cost'] else 'deny', request)


if __name__ == "__main__":
    print(run())
