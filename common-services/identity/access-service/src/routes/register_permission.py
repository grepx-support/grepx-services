"""REGISTER_PERMISSION — add or relabel an entry in the permission catalogue (products seed theirs at bring-up)."""
from grepx_service import RequestContext

from dto import AccessField as F, ReasonCode, Table


def handle(ctx: RequestContext) -> None:
    perm = ctx.text(F.PERM)
    if not perm:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    ctx.emitter.submit(Table.PERMISSION_CATALOG.value, perm, "ACCEPTED", {F.PERM.value: perm, F.LABEL.value: ctx.text(F.LABEL) or perm})
    ctx.accept({F.PERM: perm})
