"""Experiment 15: LangChain reranking stage. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    rerank = RunnableLambda(lambda docs: sorted(docs, key=lambda d: d['score'], reverse=True))
    top = RunnableLambda(lambda docs: docs[0]['text'])
    return (rerank | top).invoke([
        {'text': 'keyword match', 'score': .6}, {'text': 'direct answer', 'score': .95}])


if __name__ == "__main__":
    print(run())
