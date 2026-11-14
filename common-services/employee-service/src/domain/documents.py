# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Documents an employee must hold (food-handler licence, work visa, ID, first aid...) and when they run out.
Strategy-free on purpose: one rule - expired, or expiring within the warning window."""
from __future__ import annotations

from datetime import date, timedelta

from .employee import day, text

WARN_DAYS = 30


def clean_document(raw: dict) -> dict:
    kind = text(raw.get("kind"), 60)
    if not kind:
        raise ValueError("INVALID_DOCUMENT")
    return {"doc_id": text(raw.get("doc_id"), 40), "kind": kind, "number": text(raw.get("number"), 60),
            "issued_on": day(raw.get("issued_on")), "expires_on": day(raw.get("expires_on")), "file_id": text(raw.get("file_id"), 64)}


def state(doc: dict, today: date, warn_days: int = WARN_DAYS) -> str:
    """valid | expiring | expired | no_expiry"""
    if not doc.get("expires_on"):
        return "no_expiry"
    ends = date.fromisoformat(doc["expires_on"])
    if ends < today:
        return "expired"
    return "expiring" if ends <= today + timedelta(days=warn_days) else "valid"


def needing_action(employees: list[dict], today: date, warn_days: int = WARN_DAYS) -> list[dict]:
    """Every expired or soon-expiring document of the active employees, soonest first."""
    out = []
    for e in employees:
        if not e.get("active", True):
            continue
        for doc in e.get("documents") or []:
            s = state(doc, today, warn_days)
            if s in ("expired", "expiring"):
                out.append({"employee_id": e.get("_key") or e.get("employee_id"), "name": e.get("name", ""), **doc, "state": s})
    return sorted(out, key=lambda d: d["expires_on"])
