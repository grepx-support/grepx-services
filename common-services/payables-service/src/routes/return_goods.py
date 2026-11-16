# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RETURN_GOODS - send goods on a bill back to the supplier: up to what was billed, with why. The bill is credited
(price + tax); stock leaves the location they go back from (stock-service RETURN)."""
from grepx_service import RequestContext, new_key

from domain.returns import return_goods
from .common import run, send_back


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = ap.bill(ctx.text("bill_id"))
        key = new_key()[:12]
        out = return_goods(bill, ctx.get("lines"), ctx.text("reason"), ctx.text("note"), ctx.text("date") or ap.today(), ctx.text("actor_name"), key)
        entry = out["returns"][-1]
        send_back(ctx, ap.tenant, key, ctx.text("location_id"), [{"item_id": l["item_id"], "qty": float(l["qty"]), **({"serials": l["serials"]} if l.get("serials") else {})}
                                                                   for l in entry["lines"]], bill, entry)
        return {"bill": ap.save(bill["bill_id"], out), "return": entry}
    run(ctx, body)
