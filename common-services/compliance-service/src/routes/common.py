# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business guard, its checks, a record's day."""
from __future__ import annotations

from grepx_service import RequestContext

from dto import POINTS, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def plain(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_") and k != "status"}


def point(ctx: RequestContext, t: str, point_id: str) -> dict | None:
    row = ctx.read.accepted_one(POINTS, point_id) if point_id else None
    return {**plain(row), "point_id": row["_key"]} if row and row.get("tenant_id") == t and row.get("active", True) else None


def points(ctx: RequestContext, t: str, site: str = "") -> list[dict]:
    rows = ctx.read.accepted(POINTS, tenant_id=t, **({"site_id": site} if site else {}))
    return [{**plain(r), "point_id": r["_key"]} for r in rows if r.get("active", True)]
