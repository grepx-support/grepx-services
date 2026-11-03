"""SET_ROLE — one of the configured roles (member / staff / admin). Admins never demote themselves; the last admin stays."""
from grepx_service import RequestContext
from grepx_common import Roles

from dto import AccessField as F, ReasonCode
from .common import admins, current, save


def handle(ctx: RequestContext) -> None:
    user_id, role = ctx.text(F.USER_ID), ctx.text(F.ROLE)
    if not user_id:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    roles = Roles.of(ctx.cfg)
    if role not in roles.all:
        return ctx.reject(ReasonCode.UNKNOWN_ROLE)
    access = current(ctx, user_id)
    if access[F.ROLE.value] == roles.admin and role != roles.admin:
        if ctx.text(F.ACTOR_ID) == user_id:
            return ctx.reject(ReasonCode.SELF_DEMOTION)
        if admins(ctx) == [user_id]:
            return ctx.reject(ReasonCode.LAST_ADMIN)
    access[F.ROLE.value] = role
    if not roles.is_staff(role):
        access[F.STAFF_ROLE_ID.value], access[F.PERMS.value] = "", []
    save(ctx, user_id, access)
