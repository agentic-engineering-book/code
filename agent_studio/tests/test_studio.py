"""Agent Studio back end: graph compilation, oracle and a streamed mock run (no API calls)."""

import json

import pytest

pytest.importorskip("pydantic")

from studio import service  # noqa: E402
from studio.examples import MONITORS  # noqa: E402


@pytest.mark.parametrize(("spec", "code"), [
    ({"explain": "after"}, "A"),
    ({"explain": "before"}, "B"),
    ({"self_review": 1}, "B+"),
    ({"gate": "policy"}, "C"),
    ({"gate": "verifier", "verifier": {}}, "D1"),
    ({"gate": "verifier", "verifier": {"adaptive": True}}, "D2"),
])
def test_pipeline_compiles_to_architecture(spec, code):
    assert service.compile_agent(spec)[0] == code


def test_verifier_components_are_passed_through():
    _, verifier, _ = service.compile_agent(
        {"gate": "verifier", "verifier": {"components": ["policy", "bogus"], "replays": 9}})
    assert verifier.components == ("policy",)
    assert verifier.counterfactual_replays == 3


def test_example_has_a_unique_compliant_answer():
    result = service.oracle_for(MONITORS)
    assert result["label"] == "approve_purchase(supplier_id=S2)"
    assert "S3.approved" in result["decisive_facts"]


def test_streamed_mock_run_reports_events_and_outcome(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "EVENT_LOG", tmp_path)
    lines = [json.loads(x) for x in service.stream_run({
        "environment": {"state": MONITORS},
        "agents": [{"id": "d1", "name": "x", "provider": "mock", "gate": "verifier"}]})]
    kinds = [m["type"] for m in lines]
    assert kinds[0] == "batch_start" and kinds[-1] == "batch_end"
    events = [m["event"]["event"] for m in lines if m["type"] == "event"]
    for expected in ("task_start", "tool_response", "decision_proposed", "verification_start",
                     "verification", "executed_action"):
        assert expected in events
    end = next(m for m in lines if m["type"] == "run_end")
    assert end["metrics"]["correct"] is True
    # the oracle is reported to the viewer but never reaches the agent's prompt
    start = next(m for m in lines if m["type"] == "run_start")
    assert "approve_purchase(supplier_id=S2)" not in start["system_prompt"]


def test_invalid_environment_is_rejected():
    with pytest.raises(ValueError):
        service.oracle_for({"domain": "nowhere", "facts": {}})
