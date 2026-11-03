"""BOOK — confirm attendance; picks a time slot when the event has slots (capacity enforced)."""
from grepx_service import RequestContext

from domain import merge_state
from dto import ReasonCode, BookingField as F, BookingState as S
from .common import contact, event_of, existing, key_for, save, slot_check


def handle(ctx: RequestContext) -> None:
    event = event_of(ctx)
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    if event.get("state") == "completed":
        return ctx.reject(ReasonCode.EVENT_CLOSED)
    if not ctx.text(F.PERSON_ID):
        return ctx.reject(ReasonCode.MISSING_FIELD)
    key = key_for(ctx)
    reason, slot = slot_check(ctx, event, ctx.text(F.SLOT_ID), key)
    if reason:
        return ctx.reject(reason)
    reg = existing(ctx, key) or {F.EVENT_ID.value: event["_key"], F.PERSON_ID.value: ctx.text(F.PERSON_ID),
                                 F.SOURCE.value: ctx.text(F.SOURCE) or "online", F.TENANT_ID.value: event.get("tenant_id", "")}
    reg.update({k: v for k, v in contact(ctx).items() if v})
    reg[F.STATE.value] = merge_state(reg.get(F.STATE.value), S.CONFIRMED.value)
    reg.update({F.SLOT_ID.value: slot.get("_key", ""), F.SLOT_START.value: slot.get("starts_at", ""), F.SLOT_END.value: slot.get("ends_at", "")})
    save(ctx, key, reg)
