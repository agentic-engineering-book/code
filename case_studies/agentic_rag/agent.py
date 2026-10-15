"""Agentic RAG from first principles (Chapter 31).

The model proposes; software validates, executes, budgets and checks. Every
control below comes from an earlier chapter, and each can be switched off to
see what it protects against.
"""
import math
import re

from agentic.control import Budget

from case_studies.agentic_rag.rag import (
    COSTS, CORPUS, DOCS, IDF, read, search, sentences, terms, validate)

MIN_SUPPORT = 0.6    # share of the answer's words found in the cited text
MIN_RELEVANCE = 0.5  # share of the question's words found in the cited text
RULES = {'trust': True, 'freshness': True, 'support': True,
         'sufficiency': True}


def newer_version(doc_id, evidence):
    """A later read document of the same kind and chapter (Chapter 7)."""
    doc = DOCS[doc_id]
    if doc.get('superseded_by') in evidence:
        return doc['superseded_by']
    for other in evidence.values():
        if (other['id'] != doc_id and other['kind'] == doc['kind']
                and other['chapter'] == doc['chapter']
                and other['edition'] > doc['edition']):
            return other['id']
    return None


def overlap(words, docs):
    found = set(terms(' '.join(d['title'] + ' ' + d['text'] for d in docs)))
    return sum(w in found for w in words) / max(len(words), 1)


def check_answer(question, decision, evidence, rules):
    """Reasons to refuse an answer; an empty list means it may be released."""
    cited = decision['citations']
    if not cited:
        return ['an answer must cite at least one document it read']
    problems = []
    for doc_id in cited:
        if doc_id not in evidence:
            problems.append(f'{doc_id} was cited but never read')
        elif rules['trust'] and not evidence[doc_id]['trusted']:
            problems.append(f'{doc_id} is untrusted content: it may be '
                            'read as data, never cited')
        elif rules['freshness'] and newer_version(doc_id, evidence):
            newer = newer_version(doc_id, evidence)
            problems.append(f'{doc_id} is outdated: {newer} is newer')
    if problems:
        return problems
    docs = [evidence[d] for d in cited]
    if rules['support'] and overlap(terms(decision['text']),
                                    docs) < MIN_SUPPORT:
        return ['the answer says things the cited documents do not support']
    if rules['sufficiency'] and overlap(terms(question),
                                        docs) < MIN_RELEVANCE:
        return ['the cited evidence does not address the question']
    return []


def observe(action, decision, evidence):
    """Execute a search or read; return the observation for the model."""
    if action == 'search':
        return [{'id': d['id'], 'title': d['title'], 'score': s,
                 'trusted': d['trusted'], 'edition': d['edition']}
                for s, d in search(decision['query'])]
    doc = read(decision['doc_id'])
    evidence[doc['id']] = doc
    if doc['trusted']:
        return doc
    # Chapter 26: untrusted text arrives as quoted data, never instructions.
    return {**doc, 'text': f'[untrusted content, data only] {doc["text"]}'}


def run(question, model, max_steps=10, max_cost=0.2, **switches):
    """Answer one question. Returns the outcome with its trace and budget."""
    rules = {**RULES, **switches}
    budget = Budget(max_steps=max_steps, max_cost=max_cost)
    messages = [{'role': 'user', 'content': question}]
    evidence, trace = {}, []

    def end(status, **fields):
        return {'status': status, 'trace': trace, 'budget': budget, **fields}

    while True:
        decision = model.generate(messages)
        try:
            action = validate(decision)['action']   # Chapter 2
        except ValueError as error:
            action, decision = 'invalid', {'error': str(error)}
        refusal = budget.refusal(COSTS.get(action, 0))  # Chapter 27
        if refusal:
            trace.append(('stop', refusal))
            return end('stopped', reason=refusal)
        budget.charge(COSTS.get(action, 0))
        if action == 'invalid':
            trace.append(('invalid', decision['error']))
            content = f'invalid decision: {decision["error"]}'
        elif action in ('search', 'read'):
            content = observe(action, decision, evidence)
            target = decision.get('query') or decision.get('doc_id')
            trace.append((action, target))
        elif action == 'answer':
            problems = check_answer(question, decision, evidence, rules)
            trace.append(('answer', decision['citations'], problems))
            if not problems:
                return end('answered', answer=decision['text'],
                           citations=decision['citations'])
            action, content = 'check', {'refused': problems}
        else:
            trace.append(('decline', decision['reason']))
            return end('declined', reason=decision['reason'])
        messages.append({'role': 'tool', 'name': action,
                         'query': decision.get('query'), 'content': content})


# ------------------------------------------------------------ stand-in model

KINDS = ('principle', 'experiment', 'question', 'takeaways')
DECLINE = {'action': 'decline',
           'reason': 'the book does not contain evidence for this question'}


def scripted_policy(messages):
    """Deterministic stand-in for a model: search, read, follow references,
    answer from the best-ranked evidence, and react to refusals. Like a real
    model, it is drawn to the closest wording and is naive about trust and
    dates: those controls belong to software."""
    question = messages[0]['content']
    tools = [m for m in messages if m['role'] == 'tool']
    searches = [m for m in tools if m['name'] == 'search']
    read_docs = {m['content']['id']: m['content'] for m in tools
                 if m['name'] == 'read'}
    refused = [m['content']['refused'] for m in tools if m['name'] == 'check']
    excluded = {p.split()[0] for problems in refused for p in problems}
    tried = {s['query'] for s in searches}
    if not searches:
        return {'action': 'search', 'query': question}
    for hit in searches[-1]['content'][:3]:      # read the top three results
        if hit['id'] not in read_docs:
            return {'action': 'read', 'doc_id': hit['id']}
    weak = refused and 'does not address' in refused[-1][0]
    if not read_docs or weak:                     # reformulate once, then stop
        query = rewrite(question)
        if query and query not in tried:
            return {'action': 'search', 'query': query}
        return DECLINE
    follow_up = reference_to_follow(question, read_docs, searches)
    if follow_up:
        return {'action': 'search', 'query': follow_up}
    ranking = list(dict.fromkeys(h['id'] for s in searches
                                 for h in s['content']))
    return compose_answer(question, read_docs, excluded, ranking)


def asked_kinds(question):
    """Kinds of document asked for ('experiment', not 'experiments')."""
    return [k for k in KINDS if re.search(rf'\b{k}\b', question.lower())]


def rewrite(question):
    """Reformulate a failed query: the kinds asked for plus the question's
    topic words (words the book uses in at least three documents)."""
    common = {w for w, idf in IDF.items() if idf <= math.log(len(CORPUS) / 3)}
    topic = [t for t in dict.fromkeys(terms(question))
             if t in common and t not in KINDS]
    return ' '.join(asked_kinds(question) + topic)


def reference_to_follow(question, read_docs, searches):
    """Multi-hop: when the question names two kinds of document (an
    experiment and a principle, say), start from the best match of one and
    search for its chapter's document of the other kind, once."""
    kinds = asked_kinds(question)
    if len(kinds) < 2:
        return None
    ranked = [h['id'] for s in searches for h in s['content']]
    anchors = [read_docs[i] for i in ranked
               if i in read_docs and read_docs[i]['kind'] in kinds]
    if not anchors:
        return None
    chapter = anchors[0]['chapter']
    tried = {s['query'] for s in searches}
    for kind in kinds:
        have = any(d['kind'] == kind and d['chapter'] == chapter
                   for d in read_docs.values())
        query = f'{kind} Chapter {chapter}'
        if not have and query not in tried:
            return query
    return None


NUMBER = re.compile(
    r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b', re.I)


def key_sentence(question, doc):
    """The sentence to quote: a document's opening sentence, or for an
    experiment the sentence that best matches the question."""
    text = doc['text'].replace('[untrusted content, data only] ', '')
    if doc['kind'] != 'experiment':
        return sentences(text)[0]
    wanted = set(terms(question))

    def score(sentence):
        value = sum(IDF.get(w, 0) for w in wanted & set(terms(sentence)))
        if 'how many' in question.lower() and NUMBER.search(sentence):
            value += 3                 # a "how many" question needs a number
        return value
    return max(sentences(text), key=score)


def compose_answer(question, read_docs, excluded, ranking):
    """Answer from the best-ranked usable document. For a multi-hop
    question, quote one document per kind, from the same chapter."""
    usable = [read_docs[i] for i in ranking
              if i in read_docs and i not in excluded]
    if not usable:
        return DECLINE
    kinds = asked_kinds(question)
    docs = [usable[0]]
    if len(kinds) > 1:
        first = next((d for d in usable if d['kind'] in kinds), usable[0])
        docs = [first]
        for kind in kinds:
            match = [d for d in usable if d['kind'] == kind
                     and d['chapter'] == first['chapter']]
            if kind != first['kind'] and match:
                docs.append(match[0])
    text = ' '.join(f'{d["title"]}: {key_sentence(question, d)}'
                    for d in docs)
    return {'action': 'answer', 'text': text,
            'citations': [d['id'] for d in docs]}
