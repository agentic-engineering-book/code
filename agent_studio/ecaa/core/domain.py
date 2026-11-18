"""The interface every domain implements. Agents and verifiers depend only on it.

A domain supplies tools, actions, public policy rules and a *public* decision
procedure. It never supplies a domain-specific version of the agent algorithm.
Hidden information (the generated state) is reachable only through tools,
except for the oracle (``ecaa.oracle``), which is shown only to the human viewer.
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ecaa.core.types import Action, ActionSpec, Rule, RuleResult, ToolSpec


class ToolError(Exception):
    """A tool request the environment refuses (unknown tool, bad arguments)."""


@dataclass
class PolicyDecision:
    """What the public procedure prescribes for a set of facts."""

    action: Action
    decisive_rules: tuple[str, ...] = ()
    note: str = ""


@dataclass
class RiskProfile:
    commits: bool
    reversible: bool
    magnitude: float  # 0..1, domain-normalised size of the commitment
    reasons: list[str] = field(default_factory=list)


class DomainAdapter(ABC):
    name: str = "domain"
    role: str = "an operations agent"
    procedure_text: str = ""

    # --- public description -------------------------------------------------
    @abstractmethod
    def tools(self) -> list[ToolSpec]: ...

    @abstractmethod
    def actions(self) -> list[ActionSpec]: ...

    @abstractmethod
    def rules(self) -> list[Rule]: ...

    @abstractmethod
    def objective(self, state: dict) -> str: ...

    def action_spec(self, name: str) -> ActionSpec | None:
        return next((a for a in self.actions() if a.name == name), None)

    def policy_text(self) -> str:
        lines = [f"[{r.rule_id}] (governs: {', '.join(r.applies_to)}) {r.text}"
                 for r in self.rules()]
        if self.procedure_text:
            lines += ["", "Decision procedure (apply in order):", self.procedure_text.strip()]
        return "\n".join(lines)

    # --- environment ----------------------------------------------------------
    @abstractmethod
    def call_tool(self, state: dict, name: str, args: dict) -> tuple[dict, tuple[str, ...]]:
        """Return (content, authoritative fact keys). Raise ToolError if invalid."""

    @abstractmethod
    def true_facts(self, state: dict) -> dict[str, Any]:
        """All authoritative facts in the state (used only by the oracle)."""

    def apply_intervention(self, state: dict, key: str, value: Any) -> dict:
        new_state = copy.deepcopy(state)
        if key not in new_state["facts"]:
            raise KeyError(f"unknown fact {key}")
        new_state["facts"][key] = value
        return new_state

    @abstractmethod
    def perturbations(self, state: dict, key: str) -> list[Any]:
        """Candidate alternative values for a fact (for interventions)."""

    def relevant_facts(self, state: dict) -> list[str]:
        return sorted(self.true_facts(state))

    # --- public policy ---------------------------------------------------------
    @abstractmethod
    def policy_decision(self, facts: dict[str, Any]) -> PolicyDecision:
        """The public decision procedure applied to a set of facts."""

    def check_rules(self, facts: dict[str, Any], action: Action) -> list[RuleResult]:
        return [r.check(facts, action) for r in self.rules() if r.applies(action)]

    @abstractmethod
    def candidate_actions(self, facts: dict[str, Any], public: dict) -> list[Action]:
        """Concrete committing actions available in this task (e.g. one purchase
        per supplier), derived from public information only."""

    @abstractmethod
    def risk_profile(self, action: Action, facts: dict[str, Any]) -> RiskProfile: ...

    # --- deterministic test support -------------------------------------------
    @abstractmethod
    def information_plan(self, observed: dict[str, Any], state_view: dict) -> list[tuple[str, dict]]:
        """Tool calls that would gather the facts the procedure needs, given what
        has been observed. Used only by the deterministic mock model."""
