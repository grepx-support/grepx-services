# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A product's purchasing plugin, for this service's own tests: goods and suppliers in two plain tables; new costs and
returned goods go as requests to stand-in services (fixture-item-service, fixture-stock-service)."""
GOODS, SUPPLIERS, COSTS, RETURNS = "fixture_goods", "fixture_suppliers", "fixture_costs", "fixture_returns"


def goods(ctx, tenant, ids):
    rows = {i: ctx.read.accepted_one(GOODS, i) for i in ids}
    return {i: {k: r.get(k) for k in ("name", "unit", "cost", "weight")} for i, r in rows.items() if r and r.get("tenant_id") == tenant}


def supplier(ctx, tenant, supplier_id):
    row = ctx.read.accepted_one(SUPPLIERS, supplier_id)
    return row if row and row.get("tenant_id") == tenant else None


def set_costs(ctx, tenant, bill, costs):
    ctx.request(COSTS, f"recost-{bill['bill_id']}", {"action": "SET_COSTS", "tenant_id": tenant, "costs": costs}, "fixture-item-service")


def send_back(ctx, tenant, key, location_id, lines, bill, entry):
    ctx.request(RETURNS, f"ret-{key}", {"action": "RETURN", "tenant_id": tenant, "location_id": location_id, "lines": lines}, "fixture-stock-service")
