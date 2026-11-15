# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE - create a purchase order, or change a saved one (ORD-03, ORD-05, ORD-08)."""
from grepx_service import RequestContext

from domain import clean_lines
from dto import ReasonCode
from .common import business, find_supplier, holding, items, new_order, order, run, write


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        lines = clean_lines(ctx.get("lines") or [])
        if not ctx.text("po_id"):
            return new_order(ctx, biz, ctx.text("supplier_id"), ctx.text("location_id"), lines, ctx.text("note"))
        po = order(ctx, biz["_key"])
        supplier = find_supplier(ctx, biz["_key"], ctx.text("supplier_id") or po["supplier_id"])
        place = holding(ctx, biz["_key"], ctx.text("location_id") or po["location_id"])
        po.update({"lines": lines, "supplier_id": supplier["_key"], "supplier_name": supplier.get("name", ""),
                   "supplier_phone": supplier.get("phone", ""), "location_id": place["_key"],
                   "note": ctx.text("note") if ctx.get("note") is not None else po.get("note", "")})
        return write(ctx, biz, {k: v for k, v in po.items() if not k.startswith("_")},
                     supplier, place, items(ctx, biz["_key"], lines))
    run(ctx, body)
