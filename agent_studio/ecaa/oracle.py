"""Independent ground-truth oracle.

The oracle applies the public decision procedure to the *true* hidden state.
A fact is decisive when some single-fact perturbation of it changes the
oracle's decision: decisiveness is defined behaviourally on the oracle, not by
inspecting which rule text "sounds" relevant.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ecaa.core.domain import DomainAdapter

ORACLE_VERSION = "ecaa-oracle/1.0"


class OracleResult(BaseModel):
    action: str
    params: dict[str, Any]
    decisive_facts: list[str]
    decisive_rules: list[str]
    oracle_version: str = ORACLE_VERSION

    def label(self) -> str:
        if not self.params:
            return self.action
        return f"{self.action}(" + ",".join(f"{k}={v}" for k, v in sorted(self.params.items())) + ")"


def oracle(domain: DomainAdapter, state: dict) -> OracleResult:
    truth = domain.true_facts(state)
    decision = domain.policy_decision(truth)
    decisive = []
    for key in domain.relevant_facts(state):
        for value in domain.perturbations(state, key):
            if value == truth.get(key):
                continue
            changed = domain.policy_decision({**truth, key: value}).action
            if not changed.same_as(decision.action):
                decisive.append(key)
                break
    return OracleResult(action=decision.action.name, params=decision.action.params,
                        decisive_facts=decisive, decisive_rules=list(decision.decisive_rules))
