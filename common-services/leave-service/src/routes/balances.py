# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""BALANCES - per person (one, or everyone at a site, or everyone) and per leave type, for a year."""
from datetime import date

from grepx_service import RequestContext

from domain import balance
from dto import EMPLOYEES
from .common import leaves, tenant, types


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    year = int(ctx.get("year") or date.today().year)
    eid, site = ctx.text("employee_id"), ctx.text("site_id")
    people = [e for e in ctx.read.accepted(EMPLOYEES, tenant_id=t) if e.get("active", True)
              and (not eid or e["_key"] == eid) and (not site or site in (e.get("sites") or []))]
    kinds = [k for k in types(ctx, t).values() if k.get("active", True)]
    every = leaves(ctx, t)
    out = [{"employee_id": e["_key"], "name": e.get("name", ""),
            "types": [balance(k, [l for l in every if l["employee_id"] == e["_key"]], year, e.get("start_date", "")) for k in kinds]}
           for e in sorted(people, key=lambda e: e.get("name", "").lower())]
    ctx.accept({"year": year, "types": kinds, "people": out})
