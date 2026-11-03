"""Event projection helpers and the follow-up requests an event change triggers (slots, checklist)."""
from __future__ import annotations

from typing import Optional

from grepx_service import RequestContext, state_of

from dto import (CHECKLIST_REQUESTS, CHECKLIST_SERVICE, EVENTS_TABLE, SLOT_REQUESTS, SLOT_SERVICE, EventField as F)


def load(ctx: RequestContext, event_id: str) -> Optional[dict]:
    row = ctx.read.accepted_one(EVENTS_TABLE, event_id)
    return state_of(row)


def save(ctx: RequestContext, event: dict) -> None:
    images = list(event.get(F.IMAGES.value) or [])
    event[F.IMAGE_URL.value] = images[0] if images else ""
    ctx.emitter.submit(EVENTS_TABLE, event[F.EVENT_ID.value], "ACCEPTED", event)
    ctx.accept({F.EVENT_ID: event[F.EVENT_ID.value]})


def request_slots(ctx: RequestContext, event: dict, plan: Optional[dict] = None, slots: Optional[list] = None) -> None:
    ctx.request(SLOT_REQUESTS, f"gen-{event[F.EVENT_ID.value]}-{ctx.key[:8]}",
                {"action": "GENERATE", "event_id": event[F.EVENT_ID.value], "plan": plan or {}, "slots": slots or [],
                 "tenant_id": event.get(F.TENANT_ID.value, "")}, SLOT_SERVICE)


def checklist_template(ctx: RequestContext) -> str:
    """The checklist this deployment applies to a new event: the request's own, else config `events.checklist_template`."""
    return ctx.text("checklist_template") or str((ctx.cfg.get("events") or {}).get("checklist_template") or "")


def request_checklist(ctx: RequestContext, event: dict) -> None:
    assignee = dict(ctx.get(F.ASSIGNEE, {}))
    ctx.request(CHECKLIST_REQUESTS, f"apply-{event[F.EVENT_ID.value]}-{ctx.key[:8]}",
                {"action": "APPLY", "template_key": checklist_template(ctx), "ref_type": "event", "ref_id": event[F.EVENT_ID.value],
                 "ref_label": event[F.TITLE.value], "base_date": event[F.EVENT_DATE.value], "actor_id": ctx.text(F.ACTOR_ID),
                 "tenant_id": event.get(F.TENANT_ID.value, ""), **{f"assignee_{k}": v for k, v in assignee.items()}}, CHECKLIST_SERVICE)
