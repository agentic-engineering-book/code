"""Chapter 31: print the agent's step-by-step trace for chosen questions.

Run from the repository root:
  python -m case_studies.agentic_rag.show_trace q5 q7 q9
"""
import sys
import textwrap

from agentic import PolicyModel

from case_studies.agentic_rag.agent import run, scripted_policy
from case_studies.agentic_rag.questions import QUESTIONS


def wrapped(text, indent='     ', first=None):
    return textwrap.fill(text, 78, initial_indent=indent if first is None else first,
                         subsequent_indent=indent)


def show(case):
    print(wrapped(f'{case["id"]}: {case["question"]}', '    ', ''))
    outcome = run(case['question'], PolicyModel(scripted_policy))
    for step in outcome['trace']:
        if step[0] == 'answer':
            verdict = '; '.join(step[2]) if step[2] else 'accepted'
            print(f'  answer  citing {", ".join(step[1])}')
            print(wrapped(f'-> {verdict}', '          '))
        else:
            print(wrapped(f'{step[0]:7s} {step[1]}', ' ' * 10, '  '))
    final = outcome.get('answer') or outcome.get('reason')
    print(f'  => {outcome["status"]}:')
    print(wrapped(final))
    budget = outcome['budget']
    print(f'  steps {budget.steps_used}, cost {budget.cost_used:.2f}')


if __name__ == '__main__':
    wanted = sys.argv[1:] or ['q5', 'q7', 'q9']
    for case in QUESTIONS:
        if case['id'] in wanted:
            show(case)
            print()
