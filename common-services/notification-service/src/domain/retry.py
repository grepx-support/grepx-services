# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Failed sends are tried again later: after 5 minutes, then 30, then 2 hours (four tries in all). Each try is its own
row "<first key>~<try>", so the delivery log shows every try and a send is never repeated twice by accident."""
from datetime import datetime, timedelta
from typing import Callable

WAITS = (5, 30, 120)                  # minutes to wait after try 1, 2, 3
CARRIED = ("template", "channel", "recipient", "values", "ref", "tenant_id", "user_id", "auto", "attachments")


def first_key(row: dict) -> str:
    return row.get("retry_of") or row["_key"]


def next_key(row: dict) -> str:
    return f"{first_key(row)}~{int(row.get('attempt') or 1) + 1}"


def wait_over(row: dict, now: datetime) -> bool:
    attempt = int(row.get("attempt") or 1)
    if attempt > len(WAITS):
        return False
    sent = row.get("sent_at") or row.get("occurred_at") or ""
    try:
        at = datetime.fromisoformat(sent)
    except ValueError:
        return True
    if at.tzinfo is None and now.tzinfo is not None:
        at = at.replace(tzinfo=now.tzinfo)
    return now - at >= timedelta(minutes=WAITS[attempt - 1])


def due(rows: list[dict], now: datetime, tried: Callable[[str], bool]) -> list[dict]:
    """Failed sends (not test messages) whose wait is over and that were not tried again yet."""
    return [r for r in rows if r.get("delivery") == "FAILED" and r.get("action") == "SEND" and wait_over(r, now)
            and not tried(next_key(r))]


def again(row: dict) -> dict:
    """The request for the next try: the same message, one try later."""
    return {**{k: row[k] for k in CARRIED if k in row}, "action": "SEND", "attempt": int(row.get("attempt") or 1) + 1,
            "retry_of": first_key(row)}
