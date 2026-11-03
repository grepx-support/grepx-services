"""REOPEN — back to open (certificates already issued are kept)."""
from grepx_service import RequestContext

from dto import EventField as F, EventState, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    event = load(ctx, ctx.text(F.EVENT_ID))
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    if event.get(F.STATE.value) != EventState.COMPLETED.value:
        return ctx.reject(ReasonCode.NOT_COMPLETED)
    save(ctx, {**event, F.STATE.value: EventState.OPEN.value})
