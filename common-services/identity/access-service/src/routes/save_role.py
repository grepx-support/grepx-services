# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_ROLE — create or edit a volunteer role, then refresh every member's effective permissions."""
from grepx_service import RequestContext, new_key

from dto import AccessField as F, ReasonCode, Table
from .common import current, save


def handle(ctx: RequestContext) -> None:
    name = ctx.text(F.NAME)
    if not name:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    role_id = ctx.text(F.ROLE_ID) or new_key()[:12]
    catalog = {r["_key"] for r in ctx.read.accepted(Table.PERMISSION_CATALOG.value)}
    perms = sorted(p for p in ctx.get(F.PERMS, []) if not catalog or p in catalog)
    ctx.emitter.submit(Table.STAFF_ROLES.value, role_id, "ACCEPTED",
                       {F.ROLE_ID.value: role_id, F.NAME.value: name, F.DESCRIPTION.value: ctx.text(F.DESCRIPTION), F.PERMS.value: perms})
    for member in ctx.read.accepted(Table.USER_ACCESS.value, staff_role_id=role_id):
        save(ctx, member["_key"], current(ctx, member["_key"]))
    ctx.accept({F.ROLE_ID: role_id, F.PERMS: perms})
