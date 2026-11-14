# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Leave types. A business that has not set its own gets these; each can be changed or switched off."""
from __future__ import annotations

DEFAULTS = [
    {"type_id": "annual", "name": "Annual leave", "days_per_year": 18, "paid": True, "carry_over": 6, "unlimited": False},
    {"type_id": "sick", "name": "Sick leave", "days_per_year": 12, "paid": True, "carry_over": 0, "unlimited": False},
    {"type_id": "casual", "name": "Casual leave", "days_per_year": 6, "paid": True, "carry_over": 0, "unlimited": False},
    {"type_id": "unpaid", "name": "Unpaid leave", "days_per_year": 0, "paid": False, "carry_over": 0, "unlimited": True},
]


def clean_type(raw: dict) -> dict:
    name = " ".join(str(raw.get("name") or "").split())[:40]
    if not name:
        raise ValueError("INVALID_NAME")
    try:
        days, carry = float(raw.get("days_per_year") or 0), float(raw.get("carry_over") or 0)
    except (TypeError, ValueError):
        raise ValueError("INVALID_DAYS")
    if not (0 <= days <= 366 and 0 <= carry <= 366):
        raise ValueError("INVALID_DAYS")
    type_id = "".join(c for c in str(raw.get("type_id") or name).lower().replace(" ", "_") if c.isalnum() or c == "_")[:30]
    return {"type_id": type_id, "name": name, "days_per_year": days, "paid": bool(raw.get("paid", True)), "carry_over": carry,
            "unlimited": bool(raw.get("unlimited")), "active": bool(raw.get("active", True))}
