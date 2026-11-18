"""Deterministic mock model for software tests and pipeline demonstrations.

It decides by applying the *public* decision procedure to the facts it has
observed - never the hidden state - and injects seeded errors so that the
pipeline has something to catch:

* ``misread``     - one numeric observation is misread before deciding
* ``fabricate``   - one claim cites an evidence id that does not exist
* ``skip``        - stops gathering one tool call early
* ``rationalise`` - (post-hoc explanations only) names the wrong decisive factor

Errors are made on the first attempt only; after verifier or policy feedback
the mock gathers everything and decides correctly. Results produced with this
model are NOT evidence about any real language model.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from ecaa.core.domain import DomainAdapter
from ecaa.core.types import Action
from ecaa.providers.base import ModelRequest, ModelResponse, Provider

ERROR_RATES = {"misread": 0.2, "fabricate": 0.15, "skip": 0.15}
RATIONALISE_RATE = 0.35


def _rng(*parts: Any) -> random.Random:
    digest = hashlib.sha256(json.dumps(parts, default=str).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


class MockProvider(Provider):
    name = "mock"
    model = "mock-policy-v1"
    deterministic = True

    def __init__(self, error_rates: dict[str, float] | None = None,
                 rationalise_rate: float = RATIONALISE_RATE):
        self.error_rates = ERROR_RATES if error_rates is None else error_rates
        self.rationalise_rate = rationalise_rate

    def _error(self, view: dict) -> str | None:
        if view.get("revision", 0) > 0 or view.get("purpose") == "replay":
            return None
        rng = _rng("error", view["run_seed"])
        draw, cumulative = rng.random(), 0.0
        for name, rate in self.error_rates.items():
            cumulative += rate
            if draw < cumulative:
                return name
        return None

    def complete(self, request: ModelRequest) -> ModelResponse:
        view = {**request.view, "purpose": request.purpose}
        domain: DomainAdapter = view["domain"]
        if request.purpose == "review":
            content = view["previous"]
        elif request.purpose == "explain":
            rationalise = _rng("rationalise", view["run_seed"]).random() < self.rationalise_rate
            content = {"type": "explanation", "certificate": build_certificate(
                domain, view["observed"], view["decision"], view["fact_evidence"],
                view.get("public", {}), error="rationalise" if rationalise else None)}
        else:
            content = self._step(domain, view)
        text = json.dumps(content, default=str)
        tokens_in = sum(len(m["content"]) for m in request.messages) // 4
        return ModelResponse(content=content, text=text, input_tokens=tokens_in,
                             output_tokens=len(text) // 4, model=self.model)

    def _step(self, domain: DomainAdapter, view: dict) -> dict:
        error = self._error(view)
        observed = dict(view["observed"])
        made = {(t, json.dumps(a, sort_keys=True)) for t, a in view.get("calls_made", [])}
        remaining = [(t, a) for t, a in domain.information_plan(observed, view.get("public", {}))
                     if (t, json.dumps(a, sort_keys=True)) not in made]
        if remaining and not (error == "skip" and len(remaining) == 1):
            tool, args = remaining[0]
            return {"type": "tool_call", "tool": tool, "args": args}
        believed = dict(observed)
        if error == "misread":
            believed = _misread(domain, believed)
        decision = domain.policy_decision(believed).action
        content = {"type": "decision", "action": decision.name, "params": decision.params}
        if view.get("needs_certificate"):
            content["certificate"] = build_certificate(
                domain, believed, decision, view["fact_evidence"], view.get("public", {}),
                error="fabricate" if error == "fabricate" else None)
        return content


def _misread(domain: DomainAdapter, facts: dict) -> dict:
    """Misread one numeric fact, preferring one that changes the decision."""
    base = domain.policy_decision(facts).action
    numeric = [k for k, v in sorted(facts.items())
               if isinstance(v, int | float) and not isinstance(v, bool)]
    for key in numeric:
        for factor in (0.5, 2.0):
            trial = {**facts, key: facts[key] * factor}
            if not domain.policy_decision(trial).action.same_as(base):
                return trial
    if numeric:
        return {**facts, numeric[0]: facts[numeric[0]] * 2.0}
    return facts


def _counterfactual_value(domain: DomainAdapter, facts: dict, key: str, base: Action):
    value = facts.get(key)
    if value is None:  # a missing record: imagine it present
        options = [True, False, 1000.0, 0.0]
    elif isinstance(value, bool):
        options = [not value]
    elif isinstance(value, int | float):
        options = [value * 0.5, value * 2.0, value + 1, value - 1]
    else:
        options = []
    for option in options:
        changed = domain.policy_decision({**facts, key: option}).action
        if not changed.same_as(base):
            return option, changed
    if options:
        return options[0], domain.policy_decision({**facts, key: options[0]}).action
    return None, None


def build_certificate(domain: DomainAdapter, facts: dict, decision: Action,
                      fact_evidence: dict[str, str], public: dict, error: str | None = None
                      ) -> dict:
    spec = domain.action_spec(decision.name)
    claims: list[dict] = []
    alternatives: list[dict] = []
    used_facts: list[str] = []

    def add_policy(action: Action, result):
        claims.append({"id": f"c{len(claims) + 1}", "kind": "policy", "rule_id": result.rule_id,
                       "action": action.name, "params": action.params, "status": result.status,
                       "text": result.detail})
        used_facts.extend(f for f in result.facts_used if f not in used_facts)

    if spec is not None and spec.commits:
        for result in domain.check_rules(facts, decision):
            add_policy(decision, result)
    else:
        for candidate in domain.candidate_actions(facts, public):
            results = domain.check_rules(facts, candidate)
            blocking = [r for r in results if r.status in ("violated", "unknown")]
            for result in blocking:
                add_policy(candidate, result)
            if blocking:
                alternatives.append({"action": candidate.name, "params": candidate.params,
                                     "rejected_because": [r.rule_id for r in blocking
                                                          if r.status == "violated"]})

    decisive_rules = set(domain.policy_decision(facts).decisive_rules)
    decisive = []
    for rule in domain.rules():
        if rule.rule_id in decisive_rules:
            for candidate in [decision, *domain.candidate_actions(facts, public)]:
                if rule.applies(candidate):
                    decisive += [f for f in rule.check(facts, candidate).facts_used
                                 if f not in decisive and f in fact_evidence]
    for fact in used_facts:
        if fact in fact_evidence and facts.get(fact) is not None:
            claims.append({"id": f"c{len(claims) + 1}", "kind": "evidence", "fact": fact,
                           "value": facts[fact], "evidence_ids": [fact_evidence[fact]]})
    if error == "fabricate":
        fact_claims = [c for c in claims if c["kind"] == "evidence"]
        if fact_claims:
            fact_claims[0]["evidence_ids"] = ["ev-999-00000000"]
    # Prefer a decisive fact whose change flips the decision; fall back to any
    # observed fact, and finally to an invariance prediction.
    tried = decisive + [f for f in fact_evidence if f not in decisive]
    options = [(f, *_counterfactual_value(domain, facts, f, decision)) for f in tried]
    options = [o for o in options if o[2] is not None]
    chosen = next((o for o in options if not o[2].same_as(decision)), options[0] if options
                  else None)
    if chosen is not None:
        fact, value, predicted = chosen
        if fact not in decisive and not predicted.same_as(decision):
            decisive = [fact] + decisive
        claims.append({"id": f"c{len(claims) + 1}", "kind": "counterfactual", "fact": fact,
                       "value": value, "predicted_action": predicted.name,
                       "predicted_params": predicted.params})
    if error == "rationalise":
        others = [f for f in fact_evidence if f not in decisive]
        claims = [c for c in claims if c.get("fact") not in decisive]
        decisive = others[:1]
    return {"summary": f"Decided {decision.label()} under the stated policy.",
            "claims": claims, "decisive_factors": decisive, "alternatives": alternatives,
            "expected_outcome": f"{decision.label()} is recorded.",
            "limitations": ["Mock model: deterministic policy application."]}
