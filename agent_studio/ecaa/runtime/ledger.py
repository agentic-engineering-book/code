"""Append-only evidence ledger with content hashes."""

from __future__ import annotations

from typing import Any

from ecaa.core.types import Evidence, content_hash


class EvidenceLedger:
    def __init__(self, run_id: str, task_id: str):
        self.run_id, self.task_id = run_id, task_id
        self._items: list[Evidence] = []
        self._by_id: dict[str, Evidence] = {}

    def add(self, tool: str, args: dict[str, Any], content: dict[str, Any],
            authoritative_keys: tuple[str, ...]) -> Evidence:
        step = len(self._items) + 1
        digest = content_hash({"tool": tool, "args": args, "content": content})
        evidence = Evidence(
            evidence_id=f"ev-{step:03d}-{digest[:8]}", run_id=self.run_id, task_id=self.task_id,
            step=step, tool=tool, args=dict(args), content=dict(content),
            content_hash=digest, authoritative_keys=tuple(authoritative_keys))
        self._items.append(evidence)
        self._by_id[evidence.evidence_id] = evidence
        return evidence

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def get(self, evidence_id: str) -> Evidence | None:
        return self._by_id.get(evidence_id)

    def intact(self, evidence: Evidence) -> bool:
        digest = content_hash({"tool": evidence.tool, "args": evidence.args,
                               "content": evidence.content})
        return digest == evidence.content_hash

    def observed_facts(self) -> dict[str, Any]:
        """Facts established by authoritative evidence; the latest wins."""
        facts: dict[str, Any] = {}
        for evidence in self._items:
            for key in evidence.authoritative_keys:
                if key in evidence.content:
                    facts[key] = evidence.content[key]
        return facts

    def fact_sources(self, key: str) -> list[tuple[Evidence, bool]]:
        """Every evidence item that mentions ``key``, with its authority."""
        return [(e, key in e.authoritative_keys) for e in self._items if key in e.content]

    def snapshot(self) -> list[dict]:
        return [e.model_dump() for e in self._items]
