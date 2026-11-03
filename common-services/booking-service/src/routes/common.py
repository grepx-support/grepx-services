# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Booking helpers: event/slot checks, projection writes, contact fill-in."""
from __future__ import annotations

from typing import Optional

from grepx_service import RequestContext, notify, now_iso, state_of
from grepx_service.plugins import person_table, template_for

from domain import booking_key
from dto import (EVENTS_TABLE, NOT_HOLDING, BOOKINGS_TABLE, SLOTS_TABLE, BookingField as F)
from grepx_config.deployment import link


def event_of(ctx: RequestContext) -> Optional[dict]:
    return ctx.read.accepted_one(EVENTS_TABLE, ctx.text(F.EVENT_ID))


def existing(ctx: RequestContext, key: str) -> Optional[dict]:
    row = ctx.read.accepted_one(BOOKINGS_TABLE, key)
    return state_of(row)


def key_for(ctx: RequestContext) -> str:
    return ctx.text(F.BOOKING_ID) or booking_key(ctx.text(F.EVENT_ID), ctx.text(F.PERSON_ID), ctx.text(F.EMAIL), ctx.text(F.PHONE))


def contact(ctx: RequestContext) -> dict:
    """Name/phone/email from the request, else from the person's record (config `people.table`)."""
    person = ctx.read.accepted_one(person_table(ctx.cfg), ctx.text(F.PERSON_ID)) if ctx.text(F.PERSON_ID) else None
    pick = lambda f: ctx.text(f) or (person or {}).get(f.value, "")  # noqa: E731
    return {F.NAME.value: pick(F.NAME), F.PHONE.value: pick(F.PHONE), F.EMAIL.value: pick(F.EMAIL)}


def booked(ctx: RequestContext, slot_id: str, exclude: str = "") -> int:
    return sum(1 for r in ctx.read.accepted(BOOKINGS_TABLE, slot_id=slot_id) if r.get("state") not in NOT_HOLDING and r["_key"] != exclude)


def slot_check(ctx: RequestContext, event: dict, slot_id: str, me: str, override: bool = False) -> tuple[Optional[str], dict]:
    """(reason, slot) — reason None when the slot can take this person."""
    slots = ctx.read.accepted(SLOTS_TABLE, event_id=event["_key"])
    if not slots:
        return None, {}
    if not slot_id:
        return "SLOT_REQUIRED", {}
    slot = next((s for s in slots if s["_key"] == slot_id), None)
    if slot is None:
        return "UNKNOWN_SLOT", {}
    if not override and booked(ctx, slot_id, exclude=me) >= int(slot.get("capacity") or 0):
        return "SLOT_FULL", slot
    return None, slot


def save(ctx: RequestContext, key: str, reg: dict) -> None:
    reg.setdefault(F.CREATED.value, now_iso())
    reg[F.UPDATED.value] = now_iso()
    ctx.emitter.submit(BOOKINGS_TABLE, key, "ACCEPTED", {F.BOOKING_ID.value: key, **reg})
    ctx.accept({F.BOOKING_ID: key, F.STATE: reg.get(F.STATE.value)})


def event_values(cfg, event: dict, reg: dict) -> dict:
    return {"first_name": (reg.get("name") or "").split(" ")[0], "event_title": event.get("title"), "event_date": event.get("event_date"),
            "event_time": event.get("time_slot") or "All day", "venue": event.get("venue"),
            "slot_time": f"{reg.get('slot_start', '')}–{reg.get('slot_end', '')}".strip("–"), "link": link(cfg, "event", id=event["_key"])}


def tell(ctx, role: str, event: dict, reg: dict, ref: str) -> None:
    """role = event_reminder | booking_moved; the template key comes from config `messages:`."""
    notify(ctx.emitter, template_for(ctx.emitter.cfg, role), email=reg.get("email", ""), phone=reg.get("phone", ""), values=event_values(ctx.emitter.cfg, event, reg), ref=ref,
           tenant_id=event.get("tenant_id", ""), user_id=reg.get("person_id", ""))
