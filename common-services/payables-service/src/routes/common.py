# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every payables action shares: the business it works for, its rows and the accept / reject wrapper.
A row of another business is treated as not there."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_money import cents
from grepx_service import RequestContext, state_of
from grepx_service.plugins import plugin

from dto import ReasonCode, Table


class Stop(Exception):
    """A rejection with its reason."""


class Payables:
    """One business's bills and the purchasing rows they are checked against."""

    def __init__(self, ctx: RequestContext, tenant: str):
        self.ctx, self.read, self.tenant = ctx, ctx.read, tenant
        self.business = ctx.read.accepted_one(gc.business.BUSINESSES, tenant) if tenant else None

    def today(self) -> str:
        try:
            zone = ZoneInfo((self.business or {}).get("timezone") or "UTC")
        except Exception:
            zone = timezone.utc
        return datetime.now(zone).date().isoformat()

    def mine(self, table: str, key: str, reason) -> dict:
        row = self.read.accepted_one(table, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(reason)
        return state_of(row)

    def bill(self, key: str) -> dict:
        return self.mine(Table.BILLS.value, key, ReasonCode.UNKNOWN_BILL)

    def bills(self) -> list[dict]:
        return [state_of(r) for r in self.read.accepted(Table.BILLS.value, tenant_id=self.tenant)]

    def supplier(self, key: str) -> dict:
        return plugin_supplier(self.ctx, self.tenant, key)

    def order(self, key: str) -> dict:
        return self.mine(gc.purchase.PURCHASE_ORDERS, key, ReasonCode.UNKNOWN_ORDER)

    def items(self, ids) -> dict[str, dict]:
        """The goods named on a bill (the product's purchasing plugin)."""
        return plugin_goods(self.ctx, self.tenant, ids)

    def costs(self, items: dict[str, dict], po: dict | None = None) -> dict[str, int]:
        """The price each item is expected to cost, in cents: the price agreed on the order line, else its current cost."""
        agreed = {l["item_id"]: cents(l["price"]) for l in (po or {}).get("lines") or [] if l.get("price") is not None}
        return {**{k: cents(v.get("cost") or 0) for k, v in items.items()}, **agreed}

    def save(self, key: str, row: dict) -> dict:
        row = {**row, "tenant_id": self.tenant}
        self.ctx.emitter.submit(Table.BILLS.value, key, "ACCEPTED", row)
        return row


def run(ctx: RequestContext, body) -> None:
    tenant = ctx.text("tenant_id")
    try:
        if not tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        ap = Payables(ctx, tenant)
        if ap.business is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)
        out = body(ap)
    except (Stop, ValueError) as exc:
        return ctx.reject(exc.args[0])
    ctx.accept(out)


# ---- Where supplier bills meet the product ----
"""Where supplier bills meet the product: the same `purchasing` plugin purchase-service uses (deployment.yaml ->
plugins.purchasing). This service never names a product table. From the plugin:

    goods(ctx, tenant_id, ids) -> {id: {"name", "unit", "cost", "weight"?}}   # cost in the currency's main unit
    supplier(ctx, tenant_id, supplier_id) -> {"_key", "name", ...} | None
    set_costs(ctx, tenant_id, bill, costs) -> None        optional: an approved bill's landed unit costs become the goods' costs
    send_back(ctx, tenant_id, key, location_id, lines, bill, entry) -> None   optional: goods returned leave the product's stock
"""


def port(ctx: RequestContext):
    module = plugin(ctx.cfg, "purchasing")
    if module is None:
        raise Stop(ReasonCode.NOT_CONFIGURED)
    return module


def plugin_goods(ctx: RequestContext, tenant: str, ids) -> dict:
    ids = sorted({i for i in ids if i})
    return port(ctx).goods(ctx, tenant, ids) if ids else {}


def plugin_supplier(ctx: RequestContext, tenant: str, supplier_id: str) -> dict:
    row = port(ctx).supplier(ctx, tenant, supplier_id) if supplier_id else None
    if not row:
        raise Stop(ReasonCode.UNKNOWN_SUPPLIER)
    return {**row, "_key": row.get("_key") or supplier_id}


def set_costs(ctx: RequestContext, tenant: str, bill: dict, costs: dict) -> bool:
    module = port(ctx)
    if not costs or not hasattr(module, "set_costs"):
        return False
    module.set_costs(ctx, tenant, bill, costs)
    return True


def send_back(ctx: RequestContext, tenant: str, key: str, location_id: str, lines: list, bill: dict, entry: dict) -> None:
    module = port(ctx)
    if location_id and hasattr(module, "send_back"):
        module.send_back(ctx, tenant, key, location_id, lines, bill, entry)
