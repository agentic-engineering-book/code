"""A knowledge graph of the book for the Chapter 31 agent.

Nodes are the book, its parts, chapters, author and concepts, plus every
document of the full-book corpus. Edges are typed and carry provenance:
'structural' edges come from the corpus metadata (a chapter has a principle,
an experiment belongs to a chapter, a draft is superseded), and 'extracted'
edges come from compile_graph.py, where a model proposed a relation between
two concepts and software accepted it only with a verbatim quote from a
trusted document. Exploring the graph finds documents; only reading a
document makes it citable evidence.

Build the structural graph:  python -m case_studies.agentic_rag.graph
"""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import json
import re

from case_studies.agentic_rag.rag import corpus

HERE = Path(__file__).parent
GRAPH = HERE / 'graph.json'
PARTS = [('I', 'What Is an Agent?', 1, 4),
         ('II', 'Giving Agents Abilities', 5, 10),
         ('III', 'Making Agents Think and Work', 11, 16),
         ('IV', 'Agents Working Together', 17, 21),
         ('V', 'Engineering Reliable Agents', 22, 27),
         ('VI', 'Advanced Agentic Engineering', 28, 30)]
HAS = {'question': 'has_question', 'principle': 'has_principle',
       'takeaways': 'has_takeaways', 'experiment': 'has_experiment',
       'section': 'has_section'}
INVERSE = {'has_part': 'part_of', 'has_chapter': 'in_part',
           'has_question': 'question_of', 'has_principle': 'principle_of',
           'has_takeaways': 'takeaways_of', 'has_experiment': 'in_chapter',
           'has_section': 'in_chapter', 'next_section': 'previous_section',
           'written_by': 'wrote', 'described_in': 'describes',
           'defined_by': 'defines', 'developed_in': 'develops',
           'mentioned_in': 'mentions', 'refers_to': 'referred_to_by',
           'superseded_by': 'supersedes', 'comment_on': 'has_comment',
           'names': 'named_in'}
MENTIONS_PER_CONCEPT = 8


def concept_names(term):
    """'A2A (Agent2Agent protocol)' -> ['A2A', 'Agent2Agent protocol']."""
    found = re.match(r'(.*?)\s*\((.*)\)\s*$', term)
    names = [found.group(1), found.group(2)] if found else [term]
    return [n.strip() for n in names if n.strip()]


def pattern(names):
    alternatives = '|'.join(re.escape(n) for n in names)
    return re.compile(rf'(?<![\w-])(?:{alternatives})(?:s|es)?(?![\w-])',
                      re.I)


def structural_graph():
    docs = corpus('book').docs
    nodes, edges = {}, []

    def node(node_id, kind, title, **extra):
        nodes[node_id] = {'id': node_id, 'kind': kind, 'title': title,
                          'trusted': True, **extra}

    def edge(source, relation, target, evidence=None):
        edges.append({'source': source, 'relation': relation,
                      'target': target, 'kind': 'structural',
                      'evidence': evidence})

    for doc in docs:
        node(doc['id'], doc['kind'], doc['title'], doc=True,
             trusted=doc['trusted'], chapter=doc.get('chapter'))
    titles = {}
    for doc in docs:
        found = re.match(r'Chapter (\d+), (.*?): ', doc['title'])
        if found:
            titles.setdefault(int(found.group(1)), found.group(2))
    node('book', 'book', 'Agentic Engineering from First Principles')
    node('author', 'person', 'Christiaan M. van der Walt, PhD')
    edge('book', 'written_by', 'author', 'title-page-1')
    for doc in docs:
        if doc['kind'] == 'about-author':
            edge('author', 'described_in', doc['id'])
        elif doc['trusted'] and 'van der Walt' in doc['text']:
            edge(doc['id'], 'names', 'author', doc['id'])
        if doc['kind'] == 'book-facts' and doc['trusted']:
            edge('book', 'described_in', doc['id'])
    for numeral, title, first, last in PARTS:
        node(f'part:{numeral}', 'part', f'Part {numeral}: {title}')
        edge('book', 'has_part', f'part:{numeral}')
        for n in range(first, last + 1):
            node(f'chapter:{n}', 'chapter', f'Chapter {n}: {titles[n]}',
                 chapter=n)
            edge(f'part:{numeral}', 'has_chapter', f'chapter:{n}')
    sections = defaultdict(list)
    for doc in docs:
        n = doc.get('chapter')
        if not doc['trusted']:
            edge(doc['id'], 'comment_on', f'chapter:{n}')
        elif doc.get('superseded_by'):
            edge(doc['id'], 'superseded_by', doc['superseded_by'])
        elif n in titles and doc['kind'] in HAS:
            edge(f'chapter:{n}', HAS[doc['kind']], doc['id'])
            if doc['kind'] == 'section':
                sections[n].append(doc['id'])
    edge('facts-first-edition', 'superseded_by', 'facts-current')
    for chapter_sections in sections.values():
        for a, b in zip(chapter_sections, chapter_sections[1:]):
            edge(a, 'next_section', b)
    # Cross-references written in the text: "Chapter 19", "Experiment 34".
    for doc in docs:
        if not doc['trusted'] or doc['kind'] == 'glossary':
            continue
        seen = set()
        for word, number in re.findall(r'\b(Chapter|Experiment)s? (\d+)\b',
                                       doc['text']):
            n = int(number)
            target = (f'chapter:{n}' if word == 'Chapter' and n in titles
                      else f'exp{n:02}' if word == 'Experiment' else None)
            own = target in (f'chapter:{doc.get("chapter")}', doc['id'])
            if target in nodes and not own and target not in seen:
                seen.add(target)
                edge(doc['id'], 'refers_to', target, doc['id'])
    # Concepts: the glossary's terms, where they are defined and developed,
    # and the documents that use them most.
    for doc in docs:
        if doc['kind'] != 'glossary':
            continue
        concept = 'concept:' + doc['id'].removeprefix('glossary-')
        names = concept_names(doc['term'])
        node(concept, 'concept', doc['term'], names=names)
        edge(concept, 'defined_by', doc['id'])
        for n in doc['chapters']:
            edge(concept, 'developed_in', f'chapter:{n}')
        counts = []
        regex = pattern(names)
        for other in docs:
            if other['trusted'] and other['kind'] != 'glossary':
                count = len(regex.findall(other['title'] + ' '
                                          + other['text']))
                if count:
                    counts.append((count, other['id']))
        counts.sort(key=lambda pair: -pair[0])
        for count, doc_id in counts[:MENTIONS_PER_CONCEPT]:
            edge(concept, 'mentioned_in', doc_id, doc_id)
    return {'nodes': nodes, 'edges': edges}


class Graph:
    def __init__(self, data):
        self.nodes, self.edges = data['nodes'], data['edges']
        self.out, self.into = defaultdict(list), defaultdict(list)
        for e in self.edges:
            self.out[e['source']].append(e)
            self.into[e['target']].append(e)
        self.names = {}
        for node in self.nodes.values():
            for name in [node['title']] + node.get('names', []):
                self.names.setdefault(name.lower(), node['id'])

    def resolve(self, name):
        """A node from an id, 'Chapter 19', 'Experiment 34', 'Part II', a
        concept name or a title."""
        text = name.strip()
        if text in self.nodes:
            return text
        lower = text.lower().removeprefix('concept:').strip()
        found = re.fullmatch(r'(chapter|experiment|part)\s+(\w+)', lower)
        if found:
            kind, number = found.groups()
            candidate = {'chapter': f'chapter:{number}',
                         'part': f'part:{number.upper()}',
                         'experiment': f'exp{int(number):02}'
                         if number.isdigit() else ''}[kind]
            if candidate in self.nodes:
                return candidate
        if lower in self.names:
            return self.names[lower]
        singular = lower[:-1] if lower.endswith('s') else lower
        if singular in self.names:
            return self.names[singular]
        matches = [n for key, n in self.names.items() if lower in key]
        return matches[0] if len(matches) == 1 else None

    def link(self, e, direction):
        other = e['target'] if direction == 'out' else e['source']
        relation = (e['relation'] if direction == 'out'
                    else INVERSE.get(e['relation'], e['relation'] + '_of'))
        node = self.nodes[other]
        found = {'relation': relation, 'node': other, 'title': node['title'],
                 'kind': node['kind'], 'source': e['kind']}
        if not node['trusted']:
            found['trusted'] = False
        if e.get('quote'):
            found['evidence'] = e['evidence']
        return found

    def related(self, doc_id, limit=4):
        """Documents one or two typed hops from a search hit, attached to
        the hit so the model can read them without searching (graph-
        expanded retrieval): an experiment's or section's chapter principle
        and question, a principle's experiments, cross-references, and the
        newer version of a superseded document."""
        found = []

        def add(target, relation):
            node = self.nodes.get(target)
            if node and node.get('doc') and target != doc_id and all(
                    f['id'] != target for f in found):
                found.append({'id': target, 'relation': relation,
                              'title': node['title']})
        for e in self.out[doc_id]:
            if e['relation'] == 'superseded_by':
                add(e['target'], 'newer version')
        chapters = [e['source'] for e in self.into[doc_id]
                    if e['source'].startswith('chapter:')]
        for e in self.into[doc_id]:      # a glossary entry's concept
            if e['relation'] == 'defined_by':
                chapters += [c['target'] for c in self.out[e['source']]
                             if c['relation'] == 'developed_in']
        refs = [e['target'] for e in self.out[doc_id]
                if e['relation'] == 'refers_to']
        kind = self.nodes[doc_id]['kind']
        for chapter in chapters:
            for e in self.out[chapter]:
                if kind in ('principle', 'question', 'takeaways') and (
                        e['relation'] == 'has_experiment'):
                    add(e['target'], f'experiment of {chapter}')
                elif kind not in ('principle',) and e['relation'] in (
                        'has_principle', 'has_question'):
                    add(e['target'], e['relation'].replace('has_', '')
                        + f' of {chapter}')
        for target in refs:
            if target.startswith('chapter:'):
                for e in self.out[target]:
                    if e['relation'] == 'has_principle':
                        add(e['target'], f'principle of referenced {target}')
            else:
                add(target, 'referenced')
        return found[:limit]

    def explore(self, name, limit=30):
        """A node and its typed links: what the agent sees."""
        node_id = self.resolve(name)
        if node_id is None:
            raise ValueError(f'no graph node matches {name!r}; try a '
                             'document id, "Chapter 19", "Experiment 34" or '
                             'a concept such as "agent loop"')
        node = self.nodes[node_id]
        links = ([self.link(e, 'out') for e in self.out[node_id]]
                 + [self.link(e, 'in') for e in self.into[node_id]])
        order = {'structural': 0, 'extracted': 1}
        links.sort(key=lambda l: (l['relation'] in ('mentioned_in',
                                                    'mentions'),
                                  order.get(l['source'], 2)))
        result = {'node': node_id, 'title': node['title'],
                  'kind': node['kind'], 'links': links[:limit]}
        if len(links) > limit:
            result['more_links'] = len(links) - limit
        if node.get('doc'):
            result['note'] = 'a document: read it to use it as evidence'
        return result


@lru_cache(maxsize=None)
def load():
    return Graph(json.loads(GRAPH.read_text(encoding='utf-8')))


def save(data):
    GRAPH.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n',
                     encoding='utf-8')


if __name__ == '__main__':
    data = structural_graph()
    if GRAPH.exists():      # keep relations compiled earlier
        old = json.loads(GRAPH.read_text(encoding='utf-8'))
        data['edges'] += [e for e in old['edges']
                          if e['kind'] == 'extracted']
        for node_id, node in old['nodes'].items():
            data['nodes'].setdefault(node_id, node)
        data['compiled'] = old.get('compiled')
    save(data)
    kinds = defaultdict(int)
    for e in data['edges']:
        kinds[e['relation']] += 1
    print(f'{len(data["nodes"])} nodes, {len(data["edges"])} edges')
    print(dict(sorted(kinds.items(), key=lambda pair: -pair[1])))
