"""Experiment 10 (Chapter 5): Tool failure."""
import textwrap

from agentic.live import OpenAIModel, schema


def weather(city):
    raise TimeoutError("weather service unavailable")


def hidden_call(tool, arguments):
    """BREAK: every failure becomes None, so its cause is lost."""
    try:
        return tool(**arguments)
    except Exception:
        return None


def structured_call(tool, arguments):
    """FIX: a failure becomes an observation the next decision can use."""
    try:
        return {"ok": True, "value": tool(**arguments)}
    except TimeoutError as error:
        return {"ok": False, "error": "timeout",
                "retryable": True, "message": str(error)}
    except (TypeError, ValueError) as error:
        return {"ok": False, "error": "invalid_arguments",
                "retryable": False, "message": str(error)}


model = OpenAIModel(tools=[
    schema("weather", "Get the current weather in a city.", city="the city")])

for wrapper in (hidden_call, structured_call):
    messages = [{"role": "user", "content": "What is the weather in Pretoria?"}]
    decision = model.generate(messages)
    observation = wrapper(weather, decision["arguments"])
    messages.append({"role": "assistant", "content": decision})
    messages.append({"role": "tool", "content": str(observation)})

    answer = model.generate(messages)["answer"]
    print(wrapper.__name__.upper())
    for label, text in [("observation", observation), ("answer", answer)]:
        print(textwrap.fill(f"{label}: {text}", 76, initial_indent="  ",
                            subsequent_indent="    "))
    print()
