# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A product's warehouse plugin, for this service's own tests: goods in a plain table, lots kept, picks sent as a
request to a stand-in stock service."""
ZONES = ("dry", "chilled", "frozen", "packaging")
LOTS = True
GOODS, SENT = "fixture_goods", "fixture_sent"


def goods(read, tenant, ids):
    rows = {i: read.accepted_one(GOODS, i) for i in ids}
    return {i: r for i, r in rows.items() if r and r.get("tenant_id") == tenant}


def send(ctx, tenant, pick, lines):
    ctx.request(SENT, f"pick-{pick['pick_id']}", {"action": "SEND", "tenant_id": tenant, "from_location_id": pick["from_location_id"],
                                                  "to_location_id": pick["to_location_id"], "lines": lines, "ref": pick["pick_id"]}, "fixture-stock-service")
