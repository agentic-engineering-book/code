"""Experiment 56: LangChain multimodal message representation. See framework_examples/README.md."""
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda


def run():
    message = HumanMessage(content=[{'type': 'text', 'text': 'red light'},
        {'type': 'image_url', 'image_url': {'url': 'https://example.invalid/stop-sign.png'}}])
    inspect = RunnableLambda(lambda m: [block['type'] for block in m.content])
    return inspect.invoke(message)


if __name__ == "__main__":
    print(run())
