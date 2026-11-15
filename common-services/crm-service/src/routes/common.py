# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the routes: the business guard, rows as plain dicts, the business's pipeline, a refusal from a rule."""
from __future__ import annotations

from datetime import date
from typing import Callable

from grepx_service import RequestContext, new_key, now_iso

from domain import stages_of
from dto import ACTIVITIES, CONTACTS, DEALS, PIPELINES, ReasonCode


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


def stages(ctx: RequestContext, t: str) -> list[dict]:
    return stages_of(ctx.read.accepted_one(PIPELINES, t))


def rows(ctx: RequestContext, table: str, key: str, t: str, **eq) -> list[dict]:
    return [plain(r, key) for r in ctx.read.accepted(table, tenant_id=t, **eq)]


def deals(ctx, t, **eq):
    return rows(ctx, DEALS, "deal_id", t, **eq)


def contacts(ctx, t, **eq):
    return rows(ctx, CONTACTS, "contact_id", t, **eq)


def activities(ctx, t, **eq):
    return rows(ctx, ACTIVITIES, "activity_id", t, **eq)


def today(ctx: RequestContext) -> str:
    return ctx.text("today") or date.today().isoformat()


def run(ctx: RequestContext, body: Callable[[str], dict]) -> None:
    """Guard the business, run the body, accept its fields; a rule's ValueError becomes the refusal."""
    t = tenant(ctx)
    if t is None:
        return
    try:
        ctx.accept(body(t))
    except ValueError as exc:
        ctx.reject(str(exc.args[0]))


def save(ctx: RequestContext, table: str, key: str | None, row: dict, id_name: str) -> dict:
    key = key or new_key()[:14]
    ctx.emitter.submit(table, key, "ACCEPTED", {k: v for k, v in row.items() if k != id_name})
    return {**row, id_name: key}


__all__ = ["tenant", "plain", "mine", "stages", "deals", "contacts", "activities", "today", "run", "save", "now_iso"]
