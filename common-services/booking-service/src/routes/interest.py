# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""INTEREST — 'not sure yet': record interest (guests welcome). Never downgrades an existing booking."""
from grepx_service import RequestContext

from domain import merge_state
from dto import ReasonCode, BookingField as F, BookingState as S
from .common import contact, event_of, existing, key_for, save


def handle(ctx: RequestContext) -> None:
    event = event_of(ctx)
    if event is None:
        return ctx.reject(ReasonCode.UNKNOWN_EVENT)
    if event.get("state") == "completed":
        return ctx.reject(ReasonCode.EVENT_CLOSED)
    who = contact(ctx)
    if not ctx.text(F.PERSON_ID) and not (who["phone"] or who["email"]):
        return ctx.reject(ReasonCode.MISSING_FIELD)
    key = key_for(ctx)
    reg = existing(ctx, key) or {F.EVENT_ID.value: event["_key"], F.PERSON_ID.value: ctx.text(F.PERSON_ID),
                                 F.SOURCE.value: ctx.text(F.SOURCE) or "online", F.TENANT_ID.value: event.get("tenant_id", "")}
    reg.update({k: v for k, v in who.items() if v})
    reg[F.STATE.value] = merge_state(reg.get(F.STATE.value), S.INTERESTED.value)
    save(ctx, key, reg)
