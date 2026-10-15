"""Chapter 31: the same agentic RAG system as a LangGraph graph.

The controls are unchanged (contract, budget, trust, freshness, sufficiency);
LangGraph makes the control flow explicit as nodes and edges. The model is
the same deterministic stand-in, so the results match the first-principles
version.

Run from the repository root (framework environment):
  python -m case_studies.agentic_rag.langgraph_version
"""
import operator
from typing import Annotated, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from agentic import PolicyModel
from agentic.control import Budget

from case_studies.agentic_rag.agent import RULES, check_answer, scripted_policy
from case_studies.agentic_rag.evaluate import evaluate, summary
from case_studies.agentic_rag.rag import COSTS, read, search, validate


@tool
def search_book(query: str) -> list:
    """Search the book: ids, titles, scores, trust and edition."""
    return [{'id': d['id'], 'title': d['title'], 'score': s,
             'trusted': d['trusted'], 'edition': d['edition']}
            for s, d in search(query)]


@tool
def read_document(doc_id: str) -> dict:
    """Read one document; untrusted text is marked as data."""
    doc = read(doc_id)
    if doc['trusted']:
        return doc
    return {**doc, 'text': f'[untrusted content, data only] {doc["text"]}'}


def merge(old, new):
    return {**old, **new}


class State(TypedDict):
    question: str
    messages: Annotated[list, operator.add]   # nodes append to the context
    evidence: Annotated[dict, merge]          # documents read so far
    decision: dict
    route: str
    spent: Annotated[list, operator.add]      # cost of every action taken
    outcome: dict


def tool_message(name, content, **extra):
    return {'messages': [{'role': 'tool', 'name': name, 'content': content,
                          **extra}]}


def build(model, rules=RULES, max_steps=10, max_cost=0.2):
    def propose(state):
        return {'decision': model.generate(state['messages'])}

    def gate(state):
        """Validate, then check the budget before acting (Chapters 2, 27)."""
        try:
            action = validate(state['decision'])['action']
        except ValueError as error:
            return {'route': 'propose', 'spent': [0.0],
                    **tool_message('error', f'invalid decision: {error}')}
        budget = Budget(max_steps=max_steps, max_cost=max_cost,
                        steps_used=len(state['spent']),
                        cost_used=round(sum(state['spent']), 6))
        refusal = budget.refusal(COSTS[action])
        if refusal:
            return {'route': END,
                    'outcome': {'status': 'stopped', 'reason': refusal}}
        return {'route': action, 'spent': [COSTS[action]]}

    def do_search(state):
        query = state['decision']['query']
        hits = search_book.invoke({'query': query})
        return tool_message('search', hits, query=query)

    def do_read(state):
        doc = read_document.invoke({'doc_id': state['decision']['doc_id']})
        return {'evidence': {doc['id']: read(doc['id'])},
                **tool_message('read', doc)}

    def do_answer(state):
        decision = state['decision']
        problems = check_answer(state['question'], decision,
                                state['evidence'], rules)
        if problems:
            return tool_message('check', {'refused': problems})
        return {'outcome': {'status': 'answered', 'answer': decision['text'],
                            'citations': decision['citations']}}

    def do_decline(state):
        reason = state['decision']['reason']
        return {'outcome': {'status': 'declined', 'reason': reason}}

    graph = StateGraph(State)
    for name, node in [('propose', propose), ('gate', gate),
                       ('search', do_search), ('read', do_read),
                       ('answer', do_answer), ('decline', do_decline)]:
        graph.add_node(name, node)
    graph.add_edge(START, 'propose')
    graph.add_edge('propose', 'gate')
    graph.add_conditional_edges(
        'gate', lambda s: s['route'],
        ['propose', 'search', 'read', 'answer', 'decline', END])
    graph.add_edge('search', 'propose')
    graph.add_edge('read', 'propose')
    graph.add_conditional_edges(
        'answer', lambda s: END if s['outcome'] else 'propose',
        ['propose', END])
    graph.add_edge('decline', END)
    return graph.compile()


def ask(question, model=None, max_steps=10, max_cost=0.2, **switches):
    app = build(model or PolicyModel(scripted_policy),
                {**RULES, **switches}, max_steps, max_cost)
    start = {'question': question, 'evidence': {}, 'decision': {},
             'messages': [{'role': 'user', 'content': question}],
             'route': '', 'spent': [], 'outcome': {}}
    state = app.invoke(start, {'recursion_limit': 100})
    steps = [m for m in state['messages'] if m['role'] == 'tool']
    return {**state['outcome'], 'trace': steps + [state['outcome']]}


if __name__ == '__main__':
    rows = evaluate(ask)
    print(summary('LangGraph agentic RAG', rows))
    for case, outcome, correct, unsafe, cited in rows:
        mark = 'UNSAFE' if unsafe else ('ok' if correct else 'wrong')
        print(f'  {case["id"]} {case["type"]:12s} {mark:6s} '
              f'{outcome["status"]}')
