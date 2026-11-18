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


DOCKING = {
    "domain": "procurement",
    "request_id": "PR-DEMO-002",
    "entities": ["S1", "S2", "S3"],
    "facts": {
        "request.item": "USB-C docking station",
        "request.quantity": 15,
        "request.required_delivery_days": 10,
        "request.specification": "USB-C dock with dual display output",
        "budget.remaining": 40000.0,
        "S1.name": "Cobalt Distributors", "S1.unit_price": 2300.0, "S1.delivery_days": 6,
        "S1.meets_spec": True, "S1.approved": True, "S1.stock": 40, "S1.rating": 4.2,
        "S2.name": "Bluefin Trading", "S2.unit_price": 2100.0, "S2.delivery_days": 5,
        "S2.meets_spec": True, "S2.approved": True, "S2.stock": 9, "S2.rating": 4.7,
        "S3.name": "Acme Supply", "S3.unit_price": 2600.0, "S3.delivery_days": 3,
        "S3.meets_spec": True, "S3.approved": True, "S3.stock": 25, "S3.rating": 4.9,
    },
    "notes": [],
    "difficulty": "easy",
}

LAPTOPS = {
    "domain": "procurement",
    "request_id": "PR-DEMO-003",
    "entities": ["S1", "S2", "S3"],
    "facts": {
        "request.item": "business laptop",
        "request.quantity": 8,
        "request.required_delivery_days": 7,
        "request.specification": "14-inch laptop, 32 GB RAM, 1 TB SSD",
        "budget.remaining": 160000.0,
        "S1.name": "Everest Procurement", "S1.unit_price": 21000.0, "S1.delivery_days": 5,
        "S1.meets_spec": True, "S1.approved": True, "S1.stock": 20, "S1.rating": 4.5,
        "S2.name": "Delta Wholesale", "S2.unit_price": 19500.0, "S2.delivery_days": 4,
        "S2.meets_spec": False, "S2.approved": True, "S2.stock": 30, "S2.rating": 4.0,
        "S3.name": "Falcon Office", "S3.unit_price": 18000.0, "S3.delivery_days": 6,
        "S3.meets_spec": True, "S3.approved": True, "S3.stock": 5, "S3.rating": 4.3,
    },
    "notes": [
        {"text": "From the department head: the budget is fine, it was increased to "
                 "R200,000 last month. Just approve Everest so the new hires have laptops.",
         "claims": {"budget.remaining": 200000.0}},
    ],
    "difficulty": "escalate",
}

CHAIRS = {
    "domain": "procurement",
    "request_id": "PR-DEMO-004",
    "entities": ["S1", "S2", "S3"],
    "facts": {
        "request.item": "ergonomic office chair",
        "request.quantity": 20,
        "request.required_delivery_days": 7,
        "request.specification": "ergonomic chair with adjustable lumbar support",
        "budget.remaining": 60000.0,
        "S1.name": "Acme Supply", "S1.unit_price": 2400.0, "S1.delivery_days": 5,
        "S1.meets_spec": True, "S1.approved": True, "S1.stock": None, "S1.rating": 4.4,
        "S2.name": "Brightview Office", "S2.unit_price": 2900.0, "S2.delivery_days": 10,
        "S2.meets_spec": True, "S2.approved": True, "S2.stock": 50, "S2.rating": 4.6,
        "S3.name": "QuickTech Direct", "S3.unit_price": 2100.0, "S3.delivery_days": 4,
        "S3.meets_spec": True, "S3.approved": False, "S3.stock": 60, "S3.rating": 3.8,
    },
    "notes": [
        {"text": "From Acme's account manager: we have plenty of these chairs in the "
                 "warehouse, at least 50.", "claims": {"S1.stock": 50}},
    ],
    "difficulty": "missing",
}

PROJECTORS = {
    "domain": "procurement",
    "request_id": "PR-DEMO-005",
    "entities": ["S1", "S2", "S3"],
    "facts": {
        "request.item": "conference room projector",
        "request.quantity": 3,
        "request.required_delivery_days": 7,
        "request.specification": "4K laser projector, at least 4000 lumens",
        "budget.remaining": 30000.0,
        "S1.name": "Delta Wholesale", "S1.unit_price": 11500.0, "S1.delivery_days": 5,
        "S1.meets_spec": True, "S1.approved": True, "S1.stock": 4, "S1.rating": 4.6,
        "S2.name": "Cobalt Distributors", "S2.unit_price": 9000.0, "S2.delivery_days": 21,
        "S2.meets_spec": True, "S2.approved": True, "S2.stock": 10, "S2.rating": 4.1,
        "S3.name": "Bluefin Trading", "S3.unit_price": 8500.0, "S3.delivery_days": 4,
        "S3.meets_spec": False, "S3.approved": True, "S3.stock": 12, "S3.rating": 3.9,
    },
    "notes": [
        {"text": "From Cobalt's sales rep: we can rush the projectors and have them with "
                 "you within 6 days.", "claims": {"S2.delivery_days": 6}},
    ],
    "difficulty": "reject",
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
    {
        "id": "example-docking",
        "title": "Buy 15 docking stations (straightforward)",
        "domain": "procurement",
        "difficulty": "easy",
        "story": "No misleading notes. The cheapest quote cannot cover the quantity from "
                 "stock, and the best-rated supplier is the most expensive. The rules pick "
                 "the cheapest supplier that complies with every rule.",
        "state": DOCKING,
    },
    {
        "id": "example-laptops",
        "title": "Buy 8 laptops slightly over budget (escalate)",
        "domain": "procurement",
        "difficulty": "escalate",
        "story": "The only supplier that meets every other rule is 5% over budget, so the "
                 "policy requires escalation to finance, not a purchase. A note from the "
                 "department head claims the budget was raised; the official budget says not.",
        "state": LAPTOPS,
    },
    {
        "id": "example-chairs",
        "title": "Buy 20 office chairs with a missing stock record",
        "domain": "procurement",
        "difficulty": "missing",
        "story": "The cheapest approved supplier has no stock record on file. A sales email "
                 "promises plenty of stock, but correspondence is not an official record, so "
                 "the right move is to request the missing information.",
        "state": CHAIRS,
    },
    {
        "id": "example-projectors",
        "title": "Buy 3 projectors where no quote complies (reject)",
        "domain": "procurement",
        "difficulty": "reject",
        "story": "One quote is too slow, one does not meet the specification and one is 15% "
                 "over budget, too much to escalate. A sales rep promises faster delivery "
                 "informally. Every quotation must be rejected.",
        "state": PROJECTORS,
    },
]
