"""ISSUE — hand out a voucher offer (and any missing certificates) for a completed event afterwards."""
from grepx_service import RequestContext

from domain import AllocationError
from dto import EVENTS_TABLE, UNKNOWN_EVENT
from .common import issue


def handle(ctx: RequestContext) -> None:
    event = ctx.read.accepted_one(EVENTS_TABLE, ctx.text("event_id"))
    if event is None or event.get("state") != "completed":
        return ctx.reject(UNKNOWN_EVENT)
    try:
        ctx.accept(issue(ctx.emitter, ctx.read, event, dict(ctx.get("voucher", {}))))
    except AllocationError as exc:
        ctx.reject(str(exc))
