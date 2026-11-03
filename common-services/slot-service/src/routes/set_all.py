"""SET_ALL — one capacity for every slot of an event (slots never drop below their bookings)."""
from grepx_service import RequestContext, state_of

from domain import MAX_CAPACITY
from dto import ReasonCode, SlotField as F
from .common import booked, of_event, put


def handle(ctx: RequestContext) -> None:
    value = int(ctx.get(F.VALUE, 0))
    if not 1 <= value <= MAX_CAPACITY:
        return ctx.reject(ReasonCode.TOO_HIGH)
    total = 0
    for slot in of_event(ctx, ctx.text(F.EVENT_ID)):
        capacity = max(value, booked(ctx, slot["_key"]))
        put(ctx, {**state_of(slot), F.CAPACITY.value: capacity})
        total += capacity
    ctx.accept({F.CAPACITY: total})
