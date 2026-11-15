# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Deals: open on a stage, then won or lost (with why). Value in cents. Pure."""
from __future__ import annotations

from datetime import date

from grepx_money import cents

STATES = ("open", "won", "lost")


def _day(v) -> str:
    if not v:
        return ""
    try:
        return date.fromisoformat(str(v)[:10]).isoformat()
    except ValueError:
        raise ValueError("INVALID_DATE")


def clean_deal(raw: dict, stages: list[dict], current: dict | None = None) -> dict:
    """Refuses INVALID_NAME (no title), INVALID_STAGE, INVALID_AMOUNT, INVALID_DATE."""
    cur = current or {}
    title = " ".join(str(raw.get("title", cur.get("title")) or "").split())[:120]
    if not title:
        raise ValueError("INVALID_NAME")
    stage = str(raw.get("stage") or cur.get("stage") or stages[0]["stage_id"])
    if stage not in {s["stage_id"] for s in stages}:
        raise ValueError("INVALID_STAGE")
    value = raw.get("value")
    try:
        value = cents(value) if value not in (None, "") else int(cur.get("value") or 0)
    except ValueError:
        raise ValueError("INVALID_AMOUNT")
    if value < 0:
        raise ValueError("INVALID_AMOUNT")
    keep = lambda k: str(raw.get(k) if raw.get(k) is not None else cur.get(k) or "")  # noqa: E731
    return {**cur, "title": title, "stage": stage, "value": value, "currency": keep("currency").upper()[:3],
            "contact_id": keep("contact_id"), "company_id": keep("company_id"), "owner_id": keep("owner_id"), "owner_name": keep("owner_name"),
            "source": keep("source")[:40], "notes": keep("notes")[:2000], "expected_close": _day(raw.get("expected_close", cur.get("expected_close"))),
            "goods": [{"name": str(i.get("name") or "")[:80], "qty": float(i.get("qty") or 1)} for i in raw.get("goods", cur.get("goods")) or [] if i.get("name")][:30],
            "state": cur.get("state") or "open", "order": cur.get("order", 0)}


def move(deals: list[dict], deal_id: str, stage: str, index: int) -> list[dict]:
    """The deals of the target stage in their new order (the moved one at index); each with its new order number."""
    column = sorted((d for d in deals if d["stage"] == stage and d["deal_id"] != deal_id and d.get("state") == "open"), key=lambda d: d.get("order", 0))
    moved = next(d for d in deals if d["deal_id"] == deal_id)
    column.insert(max(0, min(index, len(column))), {**moved, "stage": stage})
    return [{**d, "order": n} for n, d in enumerate(column)]


def close(deal: dict, won: bool, reason: str, day: str) -> dict:
    if deal.get("state") != "open":
        raise ValueError("DEAL_CLOSED")
    if not won and not reason.strip():
        raise ValueError("REASON_NEEDED")
    return {**deal, "state": "won" if won else "lost", "closed_on": day, "lost_reason": "" if won else reason.strip()[:200]}


def reopen(deal: dict) -> dict:
    if deal.get("state") == "open":
        raise ValueError("DEAL_OPEN")
    return {**deal, "state": "open", "closed_on": "", "lost_reason": ""}
