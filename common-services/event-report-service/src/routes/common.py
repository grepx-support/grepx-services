"""Load everything an event report needs and write the event_reports projection."""
from grepx_service import RequestContext, now_iso
from grepx_service.plugins import plugin

from domain import build_stats
from dto import BOOKINGS_TABLE, NOTIFICATIONS_TABLE, REPORTS_TABLE, SLOTS_TABLE, TASKS_TABLE


def compute(ctx: RequestContext, event: dict) -> dict:
    read, event_id = ctx.read, event["_key"]
    bookings = read.accepted(BOOKINGS_TABLE, event_id=event_id)
    notes = [n for n in read.rows(NOTIFICATIONS_TABLE)
             if n.get("event_id") == event_id or (n.get("values") or {}).get("event_title") == event.get("title")]
    stats = build_stats(event, bookings, read.accepted(SLOTS_TABLE, event_id=event_id), notes, read.accepted(TASKS_TABLE, ref_id=event_id))
    product = plugin(ctx.cfg, "event_report")
    if product is not None:
        stats.update(product.extras(read, event, [b for b in bookings if b.get("state") == "attended"]))
    return stats


def save(ctx: RequestContext, event_id: str, report: dict) -> None:
    report["updated_at"] = now_iso()
    ctx.emitter.submit(REPORTS_TABLE, event_id, "ACCEPTED", {"event_id": event_id, **report})
    ctx.accept({"event_id": event_id})
