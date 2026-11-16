# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COMPLETE_PICK - everything picked is sent: one stock-service SEND (warehouse-out) with what was picked."""
from grepx_service import RequestContext, now_iso, state_of

from dto import PickState, ReasonCode, Table
from .common import Stop, port, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        pick = floor.mine(Table.PICKS.value, ctx.text("pick_id"), ReasonCode.UNKNOWN_PICK)
        if pick.get("state") != PickState.OPEN.value:
            raise Stop(ReasonCode.PICK_CLOSED)
        lines = [{"item_id": l["item_id"], "qty": l["picked"], **({"lot_id": l["lots"][0]["lot_id"]} if l.get("lots") else {})}
                 for l in pick["lines"] if l.get("picked", 0) > 0]
        if not lines:
            raise Stop(ReasonCode.NOTHING_PICKED)
        module = port(ctx.cfg)
        if not hasattr(module, "send"):
            raise Stop(ReasonCode.NOT_CONFIGURED)
        module.send(ctx, floor.tenant, {**state_of(pick), "pick_id": pick["_key"]}, lines)
        done = {**state_of(pick), "state": PickState.DONE.value, "done_at": now_iso(), "done_by_name": ctx.text("actor_name")}
        return {"pick": floor.save(Table.PICKS.value, pick["_key"], done)}
    run(ctx, body)
