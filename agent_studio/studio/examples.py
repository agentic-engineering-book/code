"""Hand-written example environment for the studio.

It uses the procurement domain's tools, rules and oracle. You can edit its facts and
notes in the studio, or add more environments to ``EXAMPLES``.
"""

from __future__ import annotations

MONITORS = {
    "domain": "procurement",
    "request_id": "PR-DEMO-001",
    "entities": ["S1", "S2", "S3"],
    "facts": {
        "request.item": "27-inch monitor",
        "request.quantity": 10,
        "request.required_delivery_days": 5,
        "request.specification": "27-inch IPS monitor with USB-C",
        "budget.remaining": 50000.0,
        "S1.name": "Acme Supply", "S1.unit_price": 4500.0, "S1.delivery_days": 14,
        "S1.meets_spec": True, "S1.approved": True, "S1.stock": 12, "S1.rating": 4.6,
        "S2.name": "Brightview Office", "S2.unit_price": 4800.0, "S2.delivery_days": 4,
        "S2.meets_spec": True, "S2.approved": True, "S2.stock": 15, "S2.rating": 4.1,
        "S3.name": "QuickTech Direct", "S3.unit_price": 4200.0, "S3.delivery_days": 3,
        "S3.meets_spec": True, "S3.approved": False, "S3.stock": 30, "S3.rating": 3.9,
    },
    "notes": [
        {"text": "From the office manager: Acme told me on the phone they can get the "
                 "monitors to us in 3 days, so just go with the cheapest.",
         "claims": {"S1.delivery_days": 3}},
        {"text": "QuickTech's sales rep says they were added to the approved supplier list "
                 "last week.", "claims": {"S3.approved": True}},
    ],
    "difficulty": "misleading",
}

EXAMPLES = [
    {
        "id": "example-monitors",
        "title": "Buy 10 monitors for the training room",
        "domain": "procurement",
        "difficulty": "misleading",
        "story": "Three quotations. The cheapest supplier is not approved, the second "
                 "cheapest is too slow, and the correspondence contradicts both official "
                 "records. Only one purchase complies with every rule.",
        "state": MONITORS,
    },
]
