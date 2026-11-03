"""CLONE — copy an event (details, pictures, optionally slot layout) to a new date and title; optionally its checklist."""

from grepx_service import RequestContext, local_today, now_iso

from domain import suggested_clone_date
from dto import SLOTS_TABLE, EventField as F, EventState, ReasonCode
from .common import load, request_checklist, request_slots, save


def handle(ctx: RequestContext) -> None:
    source = load(ctx, ctx.text(F.SOURCE_EVENT_ID))
    if source is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    new_date = ctx.text(F.EVENT_DATE) or suggested_clone_date(source[F.EVENT_DATE.value], local_today())
    event = {**source, F.EVENT_ID.value: ctx.text(F.EVENT_ID) or ctx.key, F.EVENT_DATE.value: new_date, F.TITLE.value: ctx.text(F.TITLE).strip() or source[F.TITLE.value], F.STATE.value: EventState.OPEN.value,
             F.COMPLETED_AT.value: "", F.COMPLETED_BY.value: "", F.VOUCHER.value: {}, F.CREATED.value: now_iso()}
    save(ctx, event)
    slots = [{k: s[k] for k in ("starts_at", "ends_at", "capacity")} for s in ctx.read.accepted(SLOTS_TABLE, event_id=source[F.EVENT_ID.value])]
    if slots and ctx.get(F.COPY_SLOTS, True):
        request_slots(ctx, event, slots=sorted(slots, key=lambda s: s["starts_at"]))
    if ctx.get(F.APPLY_CHECKLIST, False):
        request_checklist(ctx, event)
