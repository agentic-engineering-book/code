import pytest

from agentic import Agent, PolicyModel, ScriptedModel, calculator, execute, last_observation


def test_calculator():
    assert calculator('37*42') == 1554
    assert calculator('(12*7)+6') == 90


@pytest.mark.parametrize('expression', ['__import__("os")', 'x+1', '9**9**9', '1' * 300, 'delete all invoices'])
def test_calculator_rejects_unsafe_input(expression):
    with pytest.raises(ValueError):
        calculator(expression)


def test_execute_rejects_unknown_action():
    with pytest.raises(ValueError):
        execute({'action': 'shell', 'arguments': {}})


def test_agent_runs_scripted_decisions():
    model = ScriptedModel([{'action': 'calculator', 'arguments': {'expression': '6*7'}},
                           {'done': True, 'answer': '42'}])
    assert Agent(model).run('6*7?') == '42'


def test_scripted_model_repeats_last_response_and_agent_stops():
    model = ScriptedModel([{'action': 'calculator', 'arguments': {'expression': '1+1'}}])
    with pytest.raises(RuntimeError, match='Step limit'):
        Agent(model, max_steps=3).run('loop')
    assert model.calls == 3


def test_policy_model_reacts_to_observations():
    def policy(messages):
        seen = last_observation(messages)
        if seen is None:
            return {'action': 'calculator', 'arguments': {'expression': '6*7'}}
        return {'done': True, 'answer': seen}
    assert Agent(PolicyModel(policy)).run('6*7?') == '42'
