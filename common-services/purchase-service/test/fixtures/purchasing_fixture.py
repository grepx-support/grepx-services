# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A product's purchasing plugin, for this service's own tests: goods and suppliers in two plain tables, goods arrive at
places marked receiving, receipt goes to a goods-in table of a stand-in stock service."""
GOODS, SUPPLIERS, GOODS_IN = "fixture_goods", "fixture_suppliers", "fixture_goods_in"


def goods(ctx, tenant, ids):
    rows = {i: ctx.read.accepted_one(GOODS, i) for i in ids}
    return {i: {"name": r["name"], "unit": r.get("unit", ""), "cost": r.get("cost", 0)} for i, r in rows.items() if r and r.get("tenant_id") == tenant}


def supplier(ctx, tenant, supplier_id):
    row = ctx.read.accepted_one(SUPPLIERS, supplier_id)
    return row if row and row.get("tenant_id") == tenant else None


def may_receive_at(place):
    return bool(place.get("receiving"))


def receive(ctx, tenant, order, lines):
    ctx.request(GOODS_IN, f"po-{order['po_id']}", {"action": "TAKE_IN", "tenant_id": tenant, "location_id": order["location_id"], "lines": lines,
                                                    "ref": order["po_id"]}, "fixture-stock-service")
