# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""GENERATE — (re)build an event's slots from a plan or an explicit list; refused once anyone has booked."""
from grepx_service import RequestContext

from domain import PlanError, plan_slots
from dto import SLOTS_TABLE, ReasonCode, SlotField as F
from .common import booked, of_event, put


def handle(ctx: RequestContext) -> None:
    event_id, plan = ctx.text(F.EVENT_ID), dict(ctx.get(F.PLAN, {}))
    try:
        wanted = list(ctx.get(F.SLOTS, [])) or plan_slots(plan.get("start", ""), plan.get("end", ""), plan.get("minutes", 0), plan.get("capacity", 0))
    except PlanError:
        return ctx.reject(ReasonCode.INVALID_PLAN)
    existing = of_event(ctx, event_id)
    if any(booked(ctx, s["_key"]) for s in existing):
        return ctx.reject(ReasonCode.HAS_BOOKINGS)
    for s in existing:
        ctx.emitter.submit(SLOTS_TABLE, s["_key"], "DELETED", {F.EVENT_ID.value: event_id})
    for i, s in enumerate(wanted):
        put(ctx, {F.SLOT_ID.value: f"{event_id}-{s['starts_at'].replace(':', '')}-{i}", F.EVENT_ID.value: event_id,
                  F.STARTS_AT.value: s["starts_at"], F.ENDS_AT.value: s["ends_at"], F.CAPACITY.value: int(s["capacity"]),
                  F.TENANT_ID.value: ctx.text(F.TENANT_ID)})
    ctx.accept({F.CAPACITY: sum(int(s["capacity"]) for s in wanted), "count": len(wanted)})
