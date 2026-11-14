# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business guard, its funds, parties and entries."""
from __future__ import annotations

from grepx_service import RequestContext

from dto import ENTRIES, FUNDS, PARTIES, ReasonCode


def tenant(ctx: RequestContext) -> str | None:
    t = ctx.text("tenant_id")
    if not t:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    return t


def plain(row: dict, key: str) -> dict:
    return {**{k: v for k, v in row.items() if not k.startswith("_") and k != "status"}, key: row["_key"]}


def mine(ctx: RequestContext, table: str, key: str, t: str) -> dict | None:
    row = ctx.read.accepted_one(table, key) if key else None
    return row if row and row.get("tenant_id") == t else None


def funds(ctx: RequestContext, t: str) -> list[dict]:
    return [plain(f, "fund_id") for f in ctx.read.accepted(FUNDS, tenant_id=t)]


def party_names(ctx: RequestContext, t: str) -> dict[str, str]:
    return {p["_key"]: p.get("name", "") for p in ctx.read.accepted(PARTIES, tenant_id=t)}


def entries(ctx: RequestContext, t: str, **equals) -> list[dict]:
    return sorted((plain(e, "entry_id") for e in ctx.read.accepted(ENTRIES, tenant_id=t, **equals)), key=lambda e: (e["date"], e.get("at", "")))
