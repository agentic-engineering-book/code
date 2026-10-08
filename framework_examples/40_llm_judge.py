"""Experiment 40: LangChain judge response parsing. See framework_examples/README.md."""
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.output_parsers import JsonOutputParser


def run():
    judge = FakeListLLM(responses=['{"score": 1, "reason": "exact match"}']) | JsonOutputParser()
    return judge.invoke('Rubric: answer must equal 42. Candidate: 42.')


if __name__ == "__main__":
    print(run())
