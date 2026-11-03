"""SET_STAFF_ROLE — attach a volunteer role (bundle of permissions); empty clears it."""
from grepx_service import RequestContext

from dto import AccessField as F, ReasonCode, Table
from .common import current, save


def handle(ctx: RequestContext) -> None:
    user_id, role_id = ctx.text(F.USER_ID), ctx.text(F.STAFF_ROLE_ID)
    if not user_id:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    if role_id and not ctx.read.accepted_one(Table.STAFF_ROLES.value, role_id):
        return ctx.reject(ReasonCode.UNKNOWN_STAFF_ROLE)
    access = current(ctx, user_id)
    access[F.STAFF_ROLE_ID.value] = role_id
    save(ctx, user_id, access)
