"""Domain-independent building blocks: tools, actions, evidence and policy rules.

Facts are named by dotted keys such as ``S1.delivery_days`` or ``order.amount``.
A tool result is a dictionary from fact keys (or free-text fields) to values.
A tool is *authoritative* for the fact keys its result may establish; a value
seen only in a non-authoritative source (an email, a note) is not a fact.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ABSTAIN = "abstain"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class ToolSpec(BaseModel):
    """A read-only information tool the agent may call."""

    model_config = ConfigDict(frozen=True)
    name: str
    description: str
    parameters: dict[str, str] = Field(default_factory=dict)  # name -> description
    read_only: bool = True


class ActionSpec(BaseModel):
    """A terminal decision. ``commits`` marks actions with real-world effect
    (payments, purchases, trades); those are gated by policy verification."""

    model_config = ConfigDict(frozen=True)
    name: str
    description: str
    parameters: dict[str, str] = Field(default_factory=dict)
    commits: bool = False


class Action(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)

    def key(self) -> tuple[str, tuple]:
        return (self.name, tuple(sorted((k, str(v)) for k, v in self.params.items())))

    def same_as(self, other: Action | None) -> bool:
        return other is not None and self.key() == other.key()

    def label(self) -> str:
        if not self.params:
            return self.name
        inner = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{self.name}({inner})"


class Evidence(BaseModel):
    """One immutable tool observation in a run's evidence ledger."""

    model_config = ConfigDict(frozen=True)
    evidence_id: str
    run_id: str
    task_id: str
    step: int
    tool: str
    args: dict[str, Any]
    content: dict[str, Any]
    content_hash: str
    authoritative_keys: tuple[str, ...] = ()


RuleStatus = Literal["satisfied", "violated", "unknown", "not_applicable"]


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    status: RuleStatus
    facts_used: tuple[str, ...] = ()
    detail: str = ""


@dataclass(frozen=True)
class Rule:
    """A public policy rule. ``check`` reads facts (observed or true) and returns
    whether ``action`` satisfies the rule. ``unknown`` means a needed fact is
    missing. Rules are the *same objects* for every agent and for the oracle."""

    rule_id: str
    text: str
    applies_to: tuple[str, ...]
    check: Callable[[dict[str, Any], Action], RuleResult] = field(compare=False)

    def applies(self, action: Action) -> bool:
        return action.name in self.applies_to
