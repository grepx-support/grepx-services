"""CREATE — new open event; optional slot plan (→ slot-service) and standard checklist (→ checklist-service)."""
from grepx_service import RequestContext, now_iso

from domain import DetailsError, clean_details
from dto import IMAGE_LIMIT, EventField as F, EventState, ReasonCode
from .common import request_checklist, request_slots, save


def handle(ctx: RequestContext) -> None:
    try:
        details = clean_details(ctx.fields)
    except DetailsError as exc:
        return ctx.reject(str(exc))
    images = list(ctx.get(F.IMAGES, []))
    if len(images) > IMAGE_LIMIT:
        return ctx.reject(ReasonCode.TOO_MANY_IMAGES)
    plan = dict(ctx.get(F.SLOT_PLAN, {}))
    if plan:
        details[F.CAPACITY.value] = 0
    event = {"capacity": 100, **details, F.EVENT_ID.value: ctx.text(F.EVENT_ID) or ctx.key, F.IMAGES.value: images,
             F.STATE.value: EventState.OPEN.value, F.TENANT_ID.value: ctx.text(F.TENANT_ID), F.CREATED.value: now_iso()}
    save(ctx, event)
    if plan:
        request_slots(ctx, event, plan=plan)
    if ctx.get(F.APPLY_CHECKLIST, False):
        request_checklist(ctx, event)
