"""SNAPSHOT — (re)compute an event's numbers; the retrospective text is kept."""
from grepx_service import RequestContext

from dto import EVENTS_TABLE, REPORTS_TABLE, RETRO_FIELDS, UNKNOWN_EVENT
from .common import compute, save


def handle(ctx: RequestContext) -> None:
    event = ctx.read.accepted_one(EVENTS_TABLE, ctx.text("event_id"))
    if event is None:
        return ctx.reject(UNKNOWN_EVENT)
    old = ctx.read.accepted_one(REPORTS_TABLE, event["_key"]) or {}
    save(ctx, event["_key"], {**{k: old.get(k, "") for k in RETRO_FIELDS}, "stats": compute(ctx, event), "title": event.get("title", "")})
