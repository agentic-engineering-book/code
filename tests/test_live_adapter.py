"""The live adapter, tested offline with a recorded-response client."""
from types import SimpleNamespace as NS

from agentic import Agent
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel


def response(content=None, call=None):
    tool_calls = None
    if call:
        name, arguments, call_id = call
        tool_calls = [NS(id=call_id, function=NS(name=name, arguments=arguments))]
    message = NS(content=content, tool_calls=tool_calls)
    return NS(choices=[NS(message=message)],
              usage=NS(prompt_tokens=10, completion_tokens=5))


class RecordedClient:
    def __init__(self, responses):
        self.responses, self.requests = list(responses), []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **request):
        self.requests.append(request)
        return self.responses.pop(0)


def test_agent_runs_with_paired_tool_call_ids():
    client = RecordedClient([
        response(call=("calculator", '{"expression": "37*42"}', "call-1")),
        response(content="37 x 42 = 1554.")])
    model = OpenAIModel("fixture", tools=[CALCULATOR_SCHEMA], client=client)
    assert Agent(model).run("What is 37 * 42?") == "37 x 42 = 1554."
    second = client.requests[1]["messages"]
    assert second[1]["tool_calls"][0]["id"] == "call-1"
    assert second[2] == {"role": "tool", "tool_call_id": "call-1",
                         "content": "1554"}
    assert len(model.calls) == 2 and model.calls[0]["input_tokens"] == 10


def test_malformed_arguments_become_a_visible_error():
    client = RecordedClient([response(call=("calculator", "{bad", "c"))])
    decision = OpenAIModel("fixture", client=client).generate(
        [{"role": "user", "content": "hi"}])
    assert decision["error"] == "malformed_arguments"
    assert decision["arguments"] is None


def test_tool_result_without_call_becomes_user_text():
    model = OpenAIModel("fixture", system="Be brief.", client=RecordedClient([]))
    api = model.to_api([{"role": "user", "content": "q"},
                        {"role": "tool", "content": "1554"}])
    assert api[0]["role"] == "system"
    assert api[-1] == {"role": "user", "content": "Tool result: 1554"}
