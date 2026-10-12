"""Connect the kernel to a real model through an OpenAI-compatible API.

Works with providers that implement Chat Completions with tool calling,
including OpenAI and local servers such as Ollama
(client=OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")).
"""
import json
import time


class OpenAIModel:
    """A real model with the same generate(messages) as the stand-ins."""

    def __init__(self, model, tools=(), system=None, client=None, **settings):
        if client is None:
            from openai import OpenAI  # optional dependency
            client = OpenAI()
        self.client, self.model = client, model
        self.tools, self.system, self.settings = list(tools), system, settings
        self.calls = []  # tokens and latency for every request

    def generate(self, messages):
        request = {"model": self.model, "messages": self.to_api(messages),
                   **self.settings}
        if self.tools:
            request["tools"] = [{"type": "function", "function": schema}
                                for schema in self.tools]
            request["parallel_tool_calls"] = False
        start = time.perf_counter()
        response = self.client.chat.completions.create(**request)
        self.calls.append({
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "seconds": round(time.perf_counter() - start, 3)})
        message = response.choices[0].message
        if not message.tool_calls:
            return {"done": True, "answer": message.content or ""}
        call = message.tool_calls[0]
        decision = {"action": call.function.name, "call_id": call.id}
        try:
            arguments = call.function.arguments or "{}"
            decision["arguments"] = json.loads(arguments)
        except json.JSONDecodeError:
            decision.update(arguments=None, error="malformed_arguments")
        return decision

    def to_api(self, messages):
        """Translate kernel messages; pair each tool result with its call."""
        api = []
        if self.system:
            api.append({"role": "system", "content": self.system})
        pending = None
        for message in messages:
            role, content = message["role"], message["content"]
            if role == "assistant" and isinstance(content, dict):
                if "call_id" in content:
                    pending = content["call_id"]
                    arguments = json.dumps(content.get("arguments") or {})
                    api.append({"role": "assistant", "content": None,
                                "tool_calls": [{
                                    "id": pending, "type": "function",
                                    "function": {"name": content["action"],
                                                 "arguments": arguments}}]})
                else:
                    api.append({"role": "assistant",
                                "content": content.get("answer", "")})
            elif role == "tool" and pending:
                api.append({"role": "tool", "tool_call_id": pending,
                            "content": str(content)})
                pending = None
            elif role == "tool":  # a result with no recorded call
                api.append({"role": "user",
                            "content": f"Tool result: {content}"})
            else:
                api.append({"role": role, "content": str(content)})
        return api


CALCULATOR_SCHEMA = {
    "name": "calculator",
    "description": "Evaluate an arithmetic expression exactly. "
                   "Supports + - * / ** and parentheses.",
    "parameters": {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
        "additionalProperties": False,
    },
}
