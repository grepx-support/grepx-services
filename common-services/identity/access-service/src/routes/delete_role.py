"""DELETE_ROLE — remove a volunteer role; members keep their personal permissions."""
from grepx_service import RequestContext

from dto import AccessField as F, ReasonCode, Table
from .common import current, save


def handle(ctx: RequestContext) -> None:
    role_id = ctx.text(F.ROLE_ID)
    if not ctx.read.accepted_one(Table.STAFF_ROLES.value, role_id):
        return ctx.reject(ReasonCode.UNKNOWN_STAFF_ROLE)
    ctx.emitter.submit(Table.STAFF_ROLES.value, role_id, "DELETED", {F.ROLE_ID.value: role_id})
    for member in ctx.read.accepted(Table.USER_ACCESS.value, staff_role_id=role_id):
        access = current(ctx, member["_key"])
        access[F.STAFF_ROLE_ID.value] = ""
        save(ctx, member["_key"], access)
