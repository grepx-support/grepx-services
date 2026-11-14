# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SETTINGS - the business's payroll country and rates (defaults + its changes), and every country on offer."""
from grepx_service import RequestContext

from domain import COUNTRIES
from .common import settings, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    ctx.accept({"settings": settings(ctx, t), "countries": [{"code": c.code, "name": c.name, "currency": c.currency} for c in COUNTRIES.values()]})
