"""Framework companions call real models; the graph tests below do not."""
import importlib
import json
import os
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'framework_examples/manifest.json').read_text())
pytest.importorskip('langchain_core')
pytest.importorskip('langgraph')
LIVE = os.environ.get('BOOK_LIVE_TESTS') == '1'


@pytest.mark.skipif(not LIVE, reason='paid model calls: set BOOK_LIVE_TESTS=1')
@pytest.mark.parametrize('case', CASES, ids=lambda c: f"{c['experiment']:02}_{c['name']}")
def test_framework_companion(case):
    pytest.importorskip('langchain_openai')
    assert importlib.import_module(case['module']).run()


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
