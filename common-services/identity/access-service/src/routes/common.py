# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Projection helpers: read and rewrite a user's access row with recomputed effective permissions."""
from grepx_service import RequestContext
from grepx_common import Roles
from dto import AccessField as F, Table


def current(ctx: RequestContext, user_id: str) -> dict:
    row = ctx.read.accepted_one(Table.USER_ACCESS.value, user_id) or {}
    return {F.ROLE.value: row.get(F.ROLE.value) or Roles.of(ctx.cfg).member, F.STAFF_ROLE_ID.value: row.get(F.STAFF_ROLE_ID.value, ""),
            F.PERMS.value: list(row.get(F.PERMS.value) or []), F.TENANT_ID.value: row.get(F.TENANT_ID.value, ctx.text(F.TENANT_ID))}


def role_perms(ctx: RequestContext, staff_role_id: str) -> list[str]:
    row = ctx.read.accepted_one(Table.STAFF_ROLES.value, staff_role_id) if staff_role_id else None
    return list(row.get(F.PERMS.value) or []) if row else []


def save(ctx: RequestContext, user_id: str, access: dict) -> None:
    access[F.EFFECTIVE.value] = Roles.of(ctx.cfg).effective_permissions(access[F.ROLE.value], access[F.PERMS.value],
                                                                         role_perms(ctx, access[F.STAFF_ROLE_ID.value]))
    ctx.emitter.submit(Table.USER_ACCESS.value, user_id, "ACCEPTED", {F.USER_ID.value: user_id, **access})


def admins(ctx: RequestContext) -> list[str]:
    return [r["_key"] for r in ctx.read.accepted(Table.USER_ACCESS.value, role=Roles.of(ctx.cfg).admin)]
