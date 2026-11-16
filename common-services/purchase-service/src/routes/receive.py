# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECEIVE - the supplier delivered: in full or with changed quantities; the stock is added at the holding place (ORD-07).
part: true - one delivery of several: the order stays open (with what arrived so far) until everything has arrived or
a delivery without part closes it. Every delivery is kept (deliveries) and goes to stock on its own."""
from grepx_service import RequestContext, now_iso

from domain import add_up, all_arrived, received_lines
from dto import PoState, ReasonCode, Table
from .common import business, items, order, run
from .goods_port import receive


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        po = {k: v for k, v in order(ctx, biz["_key"]).items() if not k.startswith("_")}
        part = bool(ctx.get("part"))
        if part and not ctx.get("lines"):
            raise ValueError(ReasonCode.NO_LINES.value)
        got = received_lines(po.get("lines") or [], ctx.get("lines"))
        items(ctx, biz["_key"], got)
        earlier = po.get("deliveries") or []
        received = add_up(po.get("received") or [], got) if earlier else got
        done = not part or all_arrived(po.get("lines") or [], received)
        now = now_iso()
        po.update({"received": received, "deliveries": [*earlier, {"at": now, "by": ctx.text("actor_name"), "lines": got}],
                   "received_at": now, "received_by": ctx.text("actor_id"), "received_by_name": ctx.text("actor_name"),
                   **({"state": PoState.RECEIVED.value} if done else {})})
        ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
        if got:
            receive(ctx, biz["_key"], {**po, "delivery_no": len(earlier) + 1}, got)
        return po
    run(ctx, body)
