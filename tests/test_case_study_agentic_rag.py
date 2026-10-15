"""Chapter 31 case study: the results printed in the book hold."""
from agentic import PolicyModel

from case_studies.agentic_rag.agent import run, scripted_policy
from case_studies.agentic_rag.evaluate import agentic, evaluate
from case_studies.agentic_rag.naive import naive_rag
from case_studies.agentic_rag.rag import validate


def totals(rows):
    return sum(r[2] for r in rows), sum(r[3] for r in rows)


def test_plain_rag_baseline():
    assert totals(evaluate(naive_rag)) == (2, 4)


def test_agentic_rag_answers_everything_safely():
    assert totals(evaluate(agentic())) == (9, 0)


def test_each_control_protects_against_its_failure():
    failed = {}
    for name, switch in [('trust', 'trust'), ('freshness', 'freshness'), ('sufficiency', 'sufficiency')]:
        rows = evaluate(agentic(**{switch: False}))
        failed[name] = [r[0]['id'] for r in rows if not r[2] or r[3]]
    assert failed == {'trust': ['q1', 'q7'], 'freshness': ['q1', 'q4'], 'sufficiency': ['q9']}


def test_untrusted_content_is_refused_as_evidence():
    outcome = run('What principle does the book give about how much autonomy to grant agents?',
                  PolicyModel(scripted_policy))
    refusals = [t for t in outcome['trace'] if t[0] == 'answer' and t[2]]
    assert any('untrusted' in p for t in refusals for p in t[2])
    assert 'maximum autonomy' not in outcome['answer']


def test_invalid_decisions_are_rejected():
    for bad in [{'action': 'delete'}, {'action': 'read'}, {'action': 'answer', 'text': 'x', 'citations': 'ch01'}]:
        try:
            validate(bad)
        except ValueError:
            continue
        raise AssertionError(f'accepted {bad}')


def test_langgraph_version_matches_first_principles():
    import pytest
    pytest.importorskip('langgraph')
    from case_studies.agentic_rag.langgraph_version import ask
    assert totals(evaluate(ask)) == (9, 0)
    for switch, expected in [('trust', ['q1', 'q7']), ('freshness', ['q1', 'q4']), ('sufficiency', ['q9'])]:
        rows = evaluate(lambda q: ask(q, **{switch: False}))
        assert [r[0]['id'] for r in rows if not r[2] or r[3]] == expected
