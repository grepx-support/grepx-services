# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Campaign plumbing: load people, send one notification per person, record the campaign."""

from grepx_common import Roles
from grepx_config.deployment import link
from grepx_service import RequestContext, notify, now_iso
from grepx_service.plugins import person_table, plugin, template_for

from dto import ACCESS_TABLE, CAMPAIGNS_TABLE


class Audience:
    """Everything an audience is chosen from: people (config person.table), the product's per-person stats, roles."""
    def __init__(self, ctx: RequestContext):
        self.product = plugin(ctx.cfg, "audience")
        self.member = Roles.of(ctx.cfg).member
        table = person_table(ctx.cfg)
        self.people = [p for p in ctx.read.accepted(table) if not str(p.get("email", "")).endswith("@no-email.local") or p.get("phone")]
        stats_table = getattr(self.product, "STATS_TABLE", "")
        self.stats = {s["_key"]: s for s in ctx.read.accepted(stats_table)} if stats_table else {}
        self.roles = {a["_key"]: a.get("role") or self.member for a in ctx.read.accepted(ACCESS_TABLE)}


def send_all(ctx: RequestContext, role: str, recipients: list[dict], values: dict, auto: bool) -> None:
    template = template_for(ctx.cfg, role)
    channels = list(ctx.get("channels", [])) or None
    for d in recipients:
        notify(ctx.emitter, template, email=d.get("email", ""), phone=d.get("phone", ""), channels=channels, auto=auto,
               values={**values, "first_name": d.get("name", "").split(" ")[0], "name": d.get("name", "")},
               ref=f"{ctx.key}-{d['_key']}", tenant_id=d.get("tenant_id", ""), user_id=d["_key"])
    ctx.emitter.submit(CAMPAIGNS_TABLE, ctx.key, "ACCEPTED", {"kind": ctx.text("action"), "template": template, "count": len(recipients),
                                                              "event_id": ctx.text("event_id"), "by": ctx.text("actor_id"), "at": now_iso()})
    ctx.accept({"count": len(recipients)})


def event_values(cfg, event: dict) -> dict:
    return {"event_title": event.get("title"), "event_date": event.get("event_date"), "event_time": event.get("time_slot") or "All day",
            "venue": event.get("venue"), "link": link(cfg, "event", id=event["_key"])}

