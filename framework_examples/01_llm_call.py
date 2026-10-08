"""Experiment 1: LangChain model invocation. See framework_examples/README.md."""
from langchain_core.language_models.fake import FakeListLLM


def run():
    model = FakeListLLM(responses=['37 x 42 is approximately 1,500.'])
    return model.invoke('What is 37 x 42?')


if __name__ == "__main__":
    print(run())
