"""CANCEL — withdraw from an event (frees the slot). An attended booking cannot be cancelled."""
from grepx_service import RequestContext

from dto import ReasonCode, BookingField as F, BookingState as S
from .common import existing, key_for, save


def handle(ctx: RequestContext) -> None:
    key = key_for(ctx)
    reg = existing(ctx, key)
    if reg is None or reg.get(F.STATE.value) == S.CANCELLED.value:
        return ctx.reject(ReasonCode.NOT_REGISTERED)
    if reg.get(F.STATE.value) == S.ATTENDED.value:
        return ctx.reject(ReasonCode.ALREADY_ATTENDED)
    reg.update({F.STATE.value: S.CANCELLED.value, F.SLOT_ID.value: "", F.SLOT_START.value: "", F.SLOT_END.value: ""})
    save(ctx, key, reg)
