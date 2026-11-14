# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CREATE_API_KEY / REVOKE_API_KEY - an organisation's keys for other systems (the BFF makes the secret; only its hash
arrives here). A revoked key stays listed as revoked and no longer signs in."""
from grepx_service import RequestContext, now_iso, state_of

from domain.api_keys import new_key_row
from dto import ReasonCode, Table


def create(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    active = [r for r in ctx.read.accepted(Table.API_KEYS.value, tenant_id=tenant) if r.get("active")] if tenant else []
    try:
        row = new_key_row({k: ctx.get(k) for k in ("key_id", "secret_hash", "scope", "name", "actor_name")}, tenant, len(active), now_iso())
    except ValueError as exc:
        return ctx.reject(str(exc))
    if ctx.read.accepted_one(Table.API_KEYS.value, row["key_id"]):
        return ctx.reject(ReasonCode.INVALID_KEY)
    ctx.emitter.submit(Table.API_KEYS.value, row["key_id"], "ACCEPTED", row)
    ctx.accept({k: v for k, v in row.items() if k != "secret_hash"})


def revoke(ctx: RequestContext) -> None:
    row = ctx.read.accepted_one(Table.API_KEYS.value, ctx.text("key_id"))
    if row is None or row.get("tenant_id") != ctx.text("tenant_id"):
        return ctx.reject(ReasonCode.UNKNOWN_KEY)
    out = {**state_of(row), "active": False, "revoked_at": now_iso(), "revoked_by": ctx.text("actor_name")[:80]}
    ctx.emitter.submit(Table.API_KEYS.value, row["_key"], "ACCEPTED", out)
    ctx.accept({k: v for k, v in out.items() if k != "secret_hash"})
