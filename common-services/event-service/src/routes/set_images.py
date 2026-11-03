"""SET_IMAGES — replace the picture list (max 3, first is the cover)."""
from grepx_service import RequestContext

from dto import IMAGE_LIMIT, EventField as F, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    event = load(ctx, ctx.text(F.EVENT_ID))
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    images = [str(i) for i in ctx.get(F.IMAGES, []) if i]
    if len(images) > IMAGE_LIMIT:
        return ctx.reject(ReasonCode.TOO_MANY_IMAGES)
    save(ctx, {**event, F.IMAGES.value: images})
