"""UPDATE — edit details (partial)."""
from grepx_service import RequestContext

from domain import DetailsError, clean_details
from dto import DETAIL_FIELDS, EventField as F, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    event = load(ctx, ctx.text(F.EVENT_ID))
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    try:
        changes = clean_details({f.value: ctx.get(f) for f in DETAIL_FIELDS if f.value in ctx.fields}, partial=True)
    except DetailsError as exc:
        return ctx.reject(str(exc))
    save(ctx, {**event, **changes})
