"""Exercise actual framework APIs against deterministic behavioral contracts."""
import importlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'framework_examples/manifest.json').read_text())
pytest.importorskip('langchain_core')
pytest.importorskip('langgraph')


@pytest.mark.parametrize('case', CASES, ids=lambda c: f"{c['experiment']:02}_{c['name']}")
def test_framework_companion(case):
    actual = importlib.import_module(case['module']).run()
    # Normalize tuples produced by graph reducers for a portable JSON contract.
    actual = json.loads(json.dumps(actual))
    if case['experiment'] == 11:
        assert len(actual) == 4
        assert all(a < b for a, b in zip(actual, actual[1:]))
    else:
        assert actual == case['expected']


def test_graph_branch_does_not_execute_denied_capability():
    from framework_examples.support import branch
    effects = []
    def protected(state):
        effects.append('sent')
        return {'value': 'sent'}
    result = branch({'protected': protected, 'deny': lambda s: {'value': 'denied'}},
                    lambda s: 'deny', 'send_email')
    assert result == 'denied'
    assert effects == []


def test_parallel_barrier_sees_all_worker_results():
    from framework_examples.support import parallel
    assert parallel({'b': lambda: 2, 'a': lambda: 1}) == [('a', 1), ('b', 2)]


def test_human_rejection_does_not_authorize_action():
    from typing import TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import interrupt, Command
    class State(TypedDict):
        executed: bool
    effects = []
    def approval(state):
        accepted = interrupt('Approve protected action?')
        if accepted is True:
            effects.append('executed')
        return {'executed': accepted is True}
    graph = StateGraph(State)
    graph.add_node('approval', approval)
    graph.add_edge(START, 'approval'); graph.add_edge('approval', END)
    app = graph.compile(checkpointer=InMemorySaver())
    config = {'configurable': {'thread_id': 'reject'}}
    paused = app.invoke({'executed': False}, config)
    assert paused['__interrupt__']
    assert effects == []
    assert app.invoke(Command(resume=False), config)['executed'] is False
    assert effects == []


@pytest.mark.parametrize('module', ['02_llm_to_agent', '22_react'])
def test_live_adapter_binds_tools_without_sending_provider_request(monkeypatch, module):
    integration = pytest.importorskip('langchain_openai')
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    bound = []
    class ProviderFixture:
        def __init__(self, **kwargs):
            assert kwargs['model'] == 'fixture-tool-model'
            assert kwargs['timeout'] == 30
        def bind_tools(self, tools):
            bound.extend(t.name for t in tools)
            return FakeMessagesListChatModel(responses=[
                AIMessage(content='', tool_calls=[{'name': 'multiply',
                    'args': {'a': 37, 'b': 42}, 'id': 'provider-fixture'}]),
                AIMessage(content='37 x 42 = 1554.')])
    monkeypatch.setenv('BOOK_MODEL', 'fixture-tool-model')
    monkeypatch.setattr(integration, 'ChatOpenAI', ProviderFixture)
    assert importlib.import_module('framework_examples.' + module).run(live=True)[-1] == '37 x 42 = 1554.'
    assert bound == ['multiply']
