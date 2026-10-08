"""Experiment 41: LangChain local lifecycle callbacks. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from langchain_core.callbacks import BaseCallbackHandler


def run():
    class Recorder(BaseCallbackHandler):
        def __init__(self):
            self.events = []
        def on_chain_start(self, serialized, inputs, **kwargs):
            self.events.append('start')
        def on_chain_end(self, outputs, **kwargs):
            self.events.append('end')
    recorder = Recorder()
    RunnableLambda(lambda x: x + 1).invoke(41, {'callbacks': [recorder]})
    return recorder.events


if __name__ == "__main__":
    print(run())
