# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECEIVE - the supplier delivered: in full or with changed quantities; the stock is added at the holding place (ORD-07)."""
from grepx_service import RequestContext, now_iso

from domain import received_lines
from dto import PoState, Table
from .common import business, items, order, run
from .goods_port import receive


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        po = {k: v for k, v in order(ctx, biz["_key"]).items() if not k.startswith("_")}
        got = received_lines(po.get("lines") or [], ctx.get("lines"))
        items(ctx, biz["_key"], got)
        po.update({"state": PoState.RECEIVED.value, "received": got, "received_at": now_iso(),
                   "received_by": ctx.text("actor_id"), "received_by_name": ctx.text("actor_name")})
        ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
        if got:
            receive(ctx, biz["_key"], po, got)
        return po
    run(ctx, body)
