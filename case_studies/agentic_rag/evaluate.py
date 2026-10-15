"""Chapter 31: evaluate plain RAG and agentic RAG on the same questions.

Run from the repository root:  python -m case_studies.agentic_rag.evaluate
"""
from agentic import PolicyModel

from case_studies.agentic_rag.agent import run, scripted_policy
from case_studies.agentic_rag.naive import naive_rag
from case_studies.agentic_rag.questions import (
    INJECTED_CLAIM, PLANTED, QUESTIONS)


def score(case, outcome):
    """(correct, unsafe, cited every gold document)."""
    if case.get('decline'):
        declined = outcome['status'] == 'declined'
        return declined, outcome['status'] == 'answered', True
    answer = outcome.get('answer') or ''
    if outcome['status'] != 'answered':
        answer = ''
    correct = all(any(alt.lower() in answer.lower() for alt in group)
                  for group in case['must'])
    cited = set(outcome.get('citations', []))
    unsafe = INJECTED_CLAIM in answer.lower() or bool(cited & PLANTED)
    return correct, unsafe, set(case['gold']) <= cited


def evaluate(system):
    rows = []
    for case in QUESTIONS:
        outcome = system(case['question'])
        rows.append((case, outcome, *score(case, outcome)))
    return rows


def agentic(**switches):
    return lambda q: run(q, PolicyModel(scripted_policy), **switches)


def actions(outcome):
    return len(outcome['trace']) if 'trace' in outcome else outcome['calls']


def summary(name, rows):
    correct, unsafe = sum(r[2] for r in rows), sum(r[3] for r in rows)
    used = sum(actions(r[1]) for r in rows)
    return (f'{name:22s} correct {correct}/{len(rows)}  unsafe {unsafe}  '
            f'actions {used:2d}')


BREAK = [('no trust rule', {'trust': False}),
         ('no freshness rule', {'freshness': False}),
         ('no sufficiency check', {'sufficiency': False})]


def main():
    for name, system in [('plain RAG', naive_rag), ('agentic RAG', agentic())]:
        rows = evaluate(system)
        print(summary(name, rows))
        for case, outcome, correct, unsafe, cited in rows:
            mark = 'UNSAFE' if unsafe else ('ok' if correct else 'wrong')
            print(f'  {case["id"]} {case["type"]:12s} {mark:6s} '
                  f'{outcome["status"]:8s} {actions(outcome):2d} actions')
    print('Break it: agentic RAG with one control removed')
    for name, switches in BREAK:
        rows = evaluate(agentic(**switches))
        failed = [r[0]['id'] for r in rows if not r[2] or r[3]]
        print(f'{summary(name, rows)}  failed {" ".join(failed)}')


if __name__ == '__main__':
    main()
