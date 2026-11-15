# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Activities: what happened (note, call, email, meeting, WhatsApp) and what is to do (task, with a due date). Pure."""
from __future__ import annotations

from datetime import datetime

KINDS = ("note", "call", "email", "meeting", "whatsapp", "task")


def clean_activity(raw: dict, at: str) -> dict:
    """Refuses INVALID_KIND, INVALID_NAME (no subject and no text), INVALID_DATE (a due that is not a date / time)."""
    kind = str(raw.get("kind") or "note")
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    subject, body = " ".join(str(raw.get("subject") or "").split())[:160], str(raw.get("body") or "")[:4000]
    if not subject and not body:
        raise ValueError("INVALID_NAME")
    due = str(raw.get("due") or "")[:16]
    if due:
        try:
            datetime.fromisoformat(due if len(due) > 10 else f"{due}T00:00")
        except ValueError:
            raise ValueError("INVALID_DATE")
    open_task = kind == "task" or bool(due)
    return {"kind": kind, "subject": subject or body[:60], "body": body, "contact_id": str(raw.get("contact_id") or ""), "deal_id": str(raw.get("deal_id") or ""),
            "due": due, "done": not open_task, "done_at": "" if open_task else at, "at": at,
            "owner_id": str(raw.get("owner_id") or ""), "owner_name": str(raw.get("owner_name") or "")[:80], "outcome": str(raw.get("outcome") or "")[:80]}


def bucket(activity: dict, today: str) -> str:
    """overdue, today or upcoming (open tasks only)."""
    day = (activity.get("due") or today)[:10]
    return "overdue" if day < today else "today" if day == today else "upcoming"
