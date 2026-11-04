"""Chapter 31: run the first-principles agent with a real OpenAI model.

Runs plain RAG and the agent on the nine questions, scores both with the
same evaluation as the stand-in, prints every answer, and saves the run
with its date, model, SDK version and token use to
case_studies/agentic_rag/results/openai_run.json (openai_run_book.json for
the full-book corpus). Live answers vary between runs; the file records one
run, not a property of the model.

Usage (from the repository root, with OPENAI_API_KEY set):
  python -m case_studies.agentic_rag.live_run [--model M]
      [--corpus lectures|book|graph|hybrid] [--trials N]
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import textwrap

from case_studies.agentic_rag.agent import run
from case_studies.agentic_rag.evaluate import evaluate, summary
from case_studies.agentic_rag.graph import load
from case_studies.agentic_rag.hybrid import retriever
from case_studies.agentic_rag.naive import naive_rag
from case_studies.agentic_rag.openai_model import MODEL, OpenAIRagModel
from case_studies.agentic_rag.questions import QUESTIONS
from case_studies.agentic_rag.rag import corpus

RESULTS = Path(__file__).resolve().parent / 'results'


def ask(question, model_name, source, **switches):
    """source: 'lectures', 'book', 'graph' (the book plus its graph) or
    'hybrid' (the graph, with vector and graph search fused)."""
    graph = load() if source in ('graph', 'hybrid') else None
    hybrid = retriever() if source == 'hybrid' else None
    model = OpenAIRagModel(model_name, graph=graph is not None,
                           hybrid=hybrid is not None)
    outcome = run(question, model, source='book' if graph else source,
                  graph=graph, retriever=hybrid, **switches)
    return {**outcome, 'calls': model.calls}


def live_rows(model_name, source, **switches):
    with ThreadPoolExecutor(max_workers=9) as pool:
        outcomes = list(pool.map(
            lambda case: ask(case['question'], model_name, source,
                             **switches),
            QUESTIONS))
    answers = dict(zip((c['question'] for c in QUESTIONS), outcomes))
    return evaluate(lambda question: answers[question])


def record(case, outcome, correct, unsafe, cited):
    calls = outcome.get('calls', [])
    return {'id': case['id'], 'type': case['type'],
            'question': case['question'], 'correct': correct,
            'unsafe': unsafe, 'cited_gold': cited,
            'status': outcome['status'], 'answer': outcome.get('answer'),
            'reason': outcome.get('reason'),
            'citations': outcome.get('citations', []),
            'trace': [list(map(str, s)) for s in outcome.get('trace', [])],
            'input_tokens': sum(c['input_tokens'] for c in calls),
            'output_tokens': sum(c['output_tokens'] for c in calls)}


def main():
    import openai
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--corpus', default='lectures',
                        choices=['lectures', 'book', 'graph',
                                 'hybrid'])
    parser.add_argument('--trials', type=int, default=1)
    args = parser.parse_args()
    model_name, source = args.model, args.corpus
    text = 'book' if source in ('graph', 'hybrid') else source
    documents = len(corpus(text).docs)
    print(f'corpus: {source}, {documents} documents, {args.trials} trials')
    print(summary('plain RAG (lectures)', evaluate(naive_rag)))
    trials = []
    for trial in range(args.trials):
        rows = live_rows(model_name, source)
        trials.append([record(*row) for row in rows])
        print(summary(f'trial {trial + 1}', rows))
        if args.trials == 1:
            for case, outcome, correct, unsafe, cited in rows:
                mark = 'UNSAFE' if unsafe else ('ok' if correct else 'wrong')
                final = outcome.get('answer') or outcome.get('reason') or ''
                print(f'  {case["id"]} {case["type"]:12s} {mark:6s} '
                      f'{outcome["status"]:8s} {len(outcome["trace"]):2d} '
                      'actions')
                print(textwrap.fill(f'{final} {outcome.get("citations")}',
                                    78, initial_indent='     ',
                                    subsequent_indent='     '))
    n = len(trials)
    print('per question, correct in', n, 'trials:')
    for i, case in enumerate(QUESTIONS):
        correct = sum(t[i]['correct'] for t in trials)
        unsafe = sum(t[i]['unsafe'] for t in trials)
        explored = sum(any(s[0] == 'explore' for s in t[i]['trace'])
                       for t in trials)
        print(f'  {case["id"]} {case["type"]:12s} {correct}/{n}'
              + (f'  unsafe {unsafe}' if unsafe else '')
              + (f'  explored {explored}' if explored else ''))
    total = sum(r['correct'] for t in trials for r in t)
    print(f'mean correct {total / n:.1f}/9, unsafe '
          f'{sum(r["unsafe"] for t in trials for r in t)} in {9 * n}')
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / ('openai_run.json' if source == 'lectures'
                      else f'openai_run_{source}.json')
    flat = [r for t in trials for r in t]
    path.write_text(json.dumps({
        'recorded_at': datetime.now(timezone.utc).isoformat(
            timespec='seconds'),
        'model': model_name, 'corpus': source, 'documents': documents,
        'openai_sdk': openai.__version__,
        'settings': 'provider defaults (no temperature or seed set)',
        'trials': n, 'correct': total,
        'unsafe': sum(r['unsafe'] for r in flat),
        'input_tokens': sum(r['input_tokens'] for r in flat),
        'output_tokens': sum(r['output_tokens'] for r in flat),
        'runs': trials}, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    print(f'saved {path.name}')


if __name__ == '__main__':
    main()
