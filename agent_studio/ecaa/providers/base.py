"""Provider-neutral model interface.

Agents send chat messages and expect one JSON object back. ``view`` carries a
structured copy of what is already in the messages (observations, policy); only
the deterministic mock model reads it. Real providers ignore it.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelRequest:
    purpose: str                      # step | explain | review | replay
    messages: list[dict[str, str]]
    view: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    content: dict[str, Any] | None
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    model: str = ""
    error: str | None = None
    retries: int = 0


@dataclass
class Pricing:
    input_per_million: float | None = None
    output_per_million: float | None = None

    def cost(self, input_tokens: int, output_tokens: int) -> float | None:
        if self.input_per_million is None or self.output_per_million is None:
            return None
        return (input_tokens * self.input_per_million
                + output_tokens * self.output_per_million) / 1e6


class Provider(ABC):
    name: str = "provider"
    model: str = ""
    deterministic: bool = False
    pricing: Pricing = Pricing()

    @abstractmethod
    def complete(self, request: ModelRequest) -> ModelResponse: ...

    def info(self) -> dict[str, Any]:
        return {"provider": self.name, "model": self.model, "deterministic": self.deterministic}


def parse_json_object(text: str) -> dict[str, Any] | None:
    """Parse a JSON object, tolerating code fences or text around it."""
    if not text:
        return None
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None
