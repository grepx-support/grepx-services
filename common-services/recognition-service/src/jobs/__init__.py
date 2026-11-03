"""Reaction: an event becomes completed → certificates (+ the event's voucher offer)."""
from grepx_service import Emitter, Reader

from domain import AllocationError
from routes.common import issue


def handle_event(app, row, cfg) -> dict:
    if row.fields.get("status") != "ACCEPTED" or row.fields.get("state") != "completed":
        return {}
    event = {**row.fields, "_key": row.key}
    try:
        return issue(Emitter(app, cfg, cause=row), Reader(app.client), event, dict(row.fields.get("voucher") or {}))
    except AllocationError:
        return issue(Emitter(app, cfg, cause=row), Reader(app.client), event, {})
