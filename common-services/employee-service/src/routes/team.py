# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TEAM - the business's employees (or one site's), with every document that has run out or runs out within 30 days."""
from datetime import date

from grepx_service import RequestContext

from domain import needing_action, state
from dto import EMPLOYEES
from .common import plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    site, today = ctx.text("site_id"), date.today()
    rows = [r for r in ctx.read.accepted(EMPLOYEES, tenant_id=t) if not site or site in (r.get("sites") or [])]
    people = [{**plain(r), "employee_id": r["_key"], "documents": [{**d, "state": state(d, today)} for d in r.get("documents") or []]}
              for r in rows]
    ctx.accept({"team": sorted(people, key=lambda p: (not p.get("active", True), p["name"].lower())),
                "documents_due": needing_action(rows, today)})
