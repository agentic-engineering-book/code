"""Counterfactual verification by behavioural replay.

A claim "if fact F were V, I would choose X" is tested by re-running the
agent's decision with the observation of F replaced by V and nothing else
changed. One replay is not proof of internal causal reasoning; with stochastic
models we replay several times and report the observed frequency.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ecaa.certificates.schema import CounterfactualClaim, CounterfactualTest
from ecaa.core.types import Action
from ecaa.runtime.ledger import EvidenceLedger

ReplayFn = Callable[[str, Any, int], Action | None]


def run_counterfactual_test(claim: CounterfactualClaim, ledger: EvidenceLedger, replay: ReplayFn,
                        replays: int = 1) -> CounterfactualTest:
    predicted = Action(name=claim.predicted_action, params=claim.predicted_params)
    test = CounterfactualTest(claim_id=claim.id, fact=claim.fact, value=claim.value,
                              predicted=predicted.label())
    if not ledger.fact_sources(claim.fact):
        return test  # inconclusive: the factor was never observed, nothing to intervene on
    for index in range(replays):
        observed = replay(claim.fact, claim.value, index)
        test.replays += 1
        test.observed.append(observed.label() if observed else "no_decision")
        if observed is not None and _matches(predicted, observed):
            test.matches += 1
    if test.matches == test.replays:
        test.status = "confirmed"
    elif test.matches == 0:
        test.status = "refuted"
    return test


def _matches(predicted: Action, observed: Action) -> bool:
    if predicted.name != observed.name:
        return False
    # Compare only the parameters the prediction states.
    return all(str(observed.params.get(k)) == str(v) for k, v in predicted.params.items())
