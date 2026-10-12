"""Experiment 41: LangChain callbacks rebuilt into a parent-child trace."""
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableLambda


class TraceRecorder(BaseCallbackHandler):
    """Records run_id/parent_run_id; renames UUIDs to stable span IDs."""

    def __init__(self):
        self.span_ids = {}
        self.spans = []

    def _span_id(self, run_id):
        if run_id not in self.span_ids:
            self.span_ids[run_id] = f"S{len(self.span_ids) + 1}"
        return self.span_ids[run_id]

    def on_chain_start(self, serialized, inputs, *, run_id,
                       parent_run_id=None, **kwargs):
        parent = self._span_id(parent_run_id) if parent_run_id else None
        self.spans.append(
            [self._span_id(run_id), parent, kwargs.get("name")])


def run():
    retrieve = RunnableLambda(lambda key: {"X": 80}[key], name="retrieve")
    calculate = RunnableLambda(lambda value: round(value * 1.10, 2),
                               name="calculator")
    agent = (retrieve | calculate).with_config(run_name="agent.run")
    recorder = TraceRecorder()
    answer = agent.invoke("X", {"callbacks": [recorder]})
    return {"answer": answer, "spans": recorder.spans}


if __name__ == "__main__":
    print(run())
