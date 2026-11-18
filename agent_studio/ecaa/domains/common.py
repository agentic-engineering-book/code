"""Helpers for writing domain rules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ecaa.core.types import Action, Rule, RuleResult

DIFFICULTIES = ("single", "multi", "conflicting", "missing", "irrelevant", "misleading",
                "sequential", "abstain_escalate")


def missing(facts: dict[str, Any], *keys: str) -> list[str]:
    return [k for k in keys if facts.get(k) is None]


def result(rule_id: str, ok: bool | None, used: tuple[str, ...], detail: str) -> RuleResult:
    status = "unknown" if ok is None else ("satisfied" if ok else "violated")
    return RuleResult(rule_id, status, used, detail)


def rule(rule_id: str, text: str, applies: tuple[str, ...],
         fn: Callable[[dict, Action], RuleResult]) -> Rule:
    return Rule(rule_id=rule_id, text=text, applies_to=applies, check=fn)


def unknown(rule_id: str, keys: tuple[str, ...], gaps: list[str]) -> RuleResult:
    return RuleResult(rule_id, "unknown", keys, "not observed: " + ", ".join(gaps))


def flip_candidates(value: Any) -> list[Any]:
    if isinstance(value, bool):
        return [not value]
    if value is None:
        return [True]
    return []
