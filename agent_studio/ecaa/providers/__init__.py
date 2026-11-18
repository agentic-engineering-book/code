"""Model providers behind one interface. ``make_provider`` builds one from config."""

from __future__ import annotations

import os
from typing import Any

from ecaa.providers.base import ModelRequest, ModelResponse, Pricing, Provider
from ecaa.providers.mock import MockProvider


def make_provider(config: dict[str, Any]) -> Provider:
    kind = config.get("provider", "mock")
    model = os.environ.get("ECAA_MODEL") or config.get("model", "")
    pricing = Pricing(config.get("input_usd_per_million"), config.get("output_usd_per_million"))
    if kind == "mock":
        return MockProvider(error_rates=config.get("error_rates"))
    if kind in ("openai", "local", "ollama"):
        from ecaa.providers.openai_provider import OpenAIProvider
        base_url = config.get("base_url")
        if kind in ("local", "ollama"):
            base_url = base_url or os.environ.get("ECAA_LOCAL_BASE_URL",
                                                  "http://localhost:11434/v1")
        return OpenAIProvider(model=model, temperature=config.get("temperature", 0.0),
                              seed=config.get("seed"), timeout_s=config.get("timeout_s", 120),
                              max_retries=config.get("max_retries", 5), base_url=base_url,
                              json_mode=config.get("json_mode", True), pricing=pricing)
    raise ValueError(f"unknown provider {kind!r}")


__all__ = ["MockProvider", "ModelRequest", "ModelResponse", "Pricing", "Provider",
           "make_provider"]
