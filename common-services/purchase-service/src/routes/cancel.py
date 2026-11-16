# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL - cancel a saved order before receipt (ORD-08). Once part of it has arrived, cancelling closes it with what came:
received, short (the rest will not come)."""
from grepx_service import RequestContext, now_iso

from dto import PoState, Table
from .common import business, order, run


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        po = {k: v for k, v in order(ctx, biz["_key"]).items() if not k.startswith("_")}
        if po.get("deliveries"):
            po.update({"state": PoState.RECEIVED.value, "short": True, "closed_at": now_iso(), "closed_by": ctx.text("actor_name")})
        else:
            po.update({"state": PoState.CANCELLED.value, "cancelled_at": now_iso(), "cancelled_by": ctx.text("actor_name")})
        ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
        return po
    run(ctx, body)
