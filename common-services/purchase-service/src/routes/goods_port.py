# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Where purchasing meets the product (Strategy by configuration): the product's `purchasing` plugin module
(deployment.yaml -> plugins.purchasing) says what its goods and suppliers are and how goods received go into stock.
This service never names a product table. The module defines:

    goods(ctx, tenant_id, ids) -> {id: {"name", "unit", "cost"}}     # every id the business's own; unknown ids left out
    supplier(ctx, tenant_id, supplier_id) -> {"_key", "name", "phone", "email"} | None
    may_receive_at(place: dict) -> bool                             # a business location goods may arrive at
    receive(ctx, tenant_id, order: dict, lines: list[dict]) -> None # request the product's stock to take the lines in
"""
from __future__ import annotations

from grepx_service import RequestContext
from grepx_service.plugins import plugin

from dto import ReasonCode


class Stop(Exception):
    pass


def port(ctx: RequestContext):
    module = plugin(ctx.cfg, "purchasing")
    if module is None:
        raise Stop(ReasonCode.NOT_CONFIGURED)
    return module


def goods(ctx: RequestContext, tenant: str, lines: list[dict]) -> dict:
    ids = sorted({l["item_id"] for l in lines})
    found = port(ctx).goods(ctx, tenant, ids)
    if any(i not in found for i in ids):
        raise Stop(ReasonCode.UNKNOWN_ITEM)
    return found


def supplier(ctx: RequestContext, tenant: str, supplier_id: str) -> dict:
    row = port(ctx).supplier(ctx, tenant, supplier_id) if supplier_id else None
    if not row:
        raise Stop(ReasonCode.UNKNOWN_SUPPLIER)
    return row


def may_receive_at(ctx: RequestContext, place: dict) -> bool:
    return bool(port(ctx).may_receive_at(place))


def receive(ctx: RequestContext, tenant: str, order: dict, lines: list[dict]) -> None:
    port(ctx).receive(ctx, tenant, order, lines)
