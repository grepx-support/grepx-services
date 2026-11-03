"""SET_PERMISSION — grant or revoke one personal permission."""
from grepx_service import RequestContext

from dto import AccessField as F, ReasonCode, Table
from .common import current, save


def handle(ctx: RequestContext) -> None:
    user_id, perm = ctx.text(F.USER_ID), ctx.text(F.PERM)
    if not user_id or not perm:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    catalog = {r["_key"] for r in ctx.read.accepted(Table.PERMISSION_CATALOG.value)}
    if catalog and perm not in catalog:
        return ctx.reject(ReasonCode.UNKNOWN_PERMISSION)
    access = current(ctx, user_id)
    perms = set(access[F.PERMS.value])
    perms.add(perm) if ctx.get(F.ENABLED, True) else perms.discard(perm)
    access[F.PERMS.value] = sorted(perms)
    save(ctx, user_id, access)
