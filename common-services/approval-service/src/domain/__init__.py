# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Approval rules, no I/O: what a request to hold looks like, and who may decide it."""
from __future__ import annotations

import re

SELF = "approval-service"


def clean_ask(raw: dict) -> dict:
    kind = str(raw.get("kind") or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,39}", kind):
        raise ValueError("INVALID_KIND")
    title = " ".join(str(raw.get("title") or "").split())[:160]
    if len(title) < 3:
        raise ValueError("INVALID_TITLE")
    perms = sorted({str(p).strip() for p in raw.get("perms") or [] if str(p).strip()})[:10]
    if not perms:
        raise ValueError("INVALID_REQUEST")
    try:
        amount = int(raw["amount"]) if raw.get("amount") not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("INVALID_REQUEST")
    details = [{"k": str(d.get("k") or "")[:40], "v": str(d.get("v") or "")[:200]} for d in (raw.get("details") or [])[:20] if isinstance(d, dict) and d.get("k")]
    return {"kind": kind, "title": title, "ref": str(raw.get("ref") or "")[:80], "amount": amount, "currency": str(raw.get("currency") or "")[:3],
            "details": details, "link": str(raw.get("link") or "")[:200], "perms": perms,
            "then": held(raw.get("then")), "otherwise": held(raw.get("otherwise"))}


def held(raw) -> dict | None:
    """{table, service, fields, note_field?}: the request to send on the decision (None: nothing to send)."""
    if not raw:
        return None
    if not isinstance(raw, dict) or not raw.get("table") or not raw.get("service") or not isinstance(raw.get("fields"), dict) or raw["service"] == SELF:
        raise ValueError("INVALID_REQUEST")
    return {"table": str(raw["table"]), "service": str(raw["service"]), "fields": raw["fields"], "note_field": str(raw.get("note_field") or "")}


def may_decide(perms_of_role: set[str], needed: list[str]) -> bool:
    return bool(perms_of_role & set(needed))


def outgoing(request: dict, approval: dict, note: str) -> dict:
    """The held request's fields as sent: on behalf of the one who asked, naming who decided."""
    fields = {**request["fields"], "tenant_id": approval["tenant_id"], "actor_id": approval["by"], "actor_name": approval["by_name"],
              "approval_id": approval["approval_id"], "approved_by": approval.get("decided_by_name", "")}
    if request.get("note_field") and note:
        fields[request["note_field"]] = note
    return fields


__all__ = ["clean_ask", "held", "may_decide", "outgoing"]
