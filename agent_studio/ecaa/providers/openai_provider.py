"""OpenAI and any OpenAI-compatible server (Ollama, vLLM, LM Studio).

Credentials come only from the environment (OPENAI_API_KEY). Nothing about
the key is logged.
"""

from __future__ import annotations

import random
import time

from ecaa.providers.base import ModelRequest, ModelResponse, Pricing, Provider, parse_json_object

_RETRYABLE = ("RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError")


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, model: str, temperature: float | None = 0.0, seed: int | None = None,
                 timeout_s: float = 120.0, max_retries: int = 5, base_url: str | None = None,
                 api_key: str | None = None, json_mode: bool = True,
                 max_output_tokens: int | None = None, pricing: Pricing | None = None,
                 client=None):
        self.model, self.temperature, self.seed = model, temperature, seed
        self.timeout_s, self.max_retries, self.json_mode = timeout_s, max_retries, json_mode
        self.max_output_tokens = max_output_tokens
        self.pricing = pricing or Pricing()
        if base_url:
            self.name = "openai-compatible"
        if client is None:
            from openai import OpenAI
            kwargs = {"timeout": timeout_s, "max_retries": 0}
            if base_url:
                kwargs.update(base_url=base_url, api_key=api_key or "local")
            client = OpenAI(**kwargs)
        self.client = client

    def info(self):
        return {**super().info(), "temperature": self.temperature, "seed": self.seed,
                "json_mode": self.json_mode,
                "seed_note": "OpenAI seeds are best-effort; outputs may still vary"}

    def complete(self, request: ModelRequest) -> ModelResponse:
        params = {"model": self.model, "messages": request.messages}
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.seed is not None:
            params["seed"] = self.seed
        if self.json_mode:
            params["response_format"] = {"type": "json_object"}
        if self.max_output_tokens:
            params["max_completion_tokens"] = self.max_output_tokens
        retries, last_error = 0, None
        while True:
            start = time.perf_counter()
            try:
                response = self.client.chat.completions.create(**params)
            except Exception as error:  # noqa: BLE001 - classify by name, provider-neutral
                last_error = f"{type(error).__name__}: {str(error)[:200]}"
                if type(error).__name__ in _RETRYABLE and retries < self.max_retries:
                    retries += 1
                    time.sleep(min(60.0, 2 ** retries + random.random()))
                    continue
                return ModelResponse(content=None, text="", model=self.model, error=last_error,
                                     retries=retries,
                                     latency_s=round(time.perf_counter() - start, 3))
            text = response.choices[0].message.content or ""
            usage = response.usage
            return ModelResponse(
                content=parse_json_object(text), text=text,
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                latency_s=round(time.perf_counter() - start, 3),
                model=getattr(response, "model", self.model) or self.model, retries=retries)
