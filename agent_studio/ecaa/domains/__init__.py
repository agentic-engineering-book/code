"""Domain registry. The studio ships one domain: procurement."""

from __future__ import annotations

from ecaa.core.domain import DomainAdapter


def get_domain(name: str) -> DomainAdapter:
    if name == "procurement":
        from ecaa.domains.procurement import ProcurementDomain
        return ProcurementDomain()
    raise KeyError(f"unknown domain {name!r}")


DOMAINS = ("procurement",)
