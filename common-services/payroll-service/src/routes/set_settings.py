# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_SETTINGS - choose the country and change any of its rates (a rate set to null goes back to the default).
Changing the country drops the old country's changes."""
from grepx_service import RequestContext

from domain import clean_change, merged
from dto import SETTINGS
from .common import tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    try:
        own = clean_change(ctx.text("country"), ctx.get("rates") or {}, ctx.read.accepted_one(SETTINGS, t))
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.emitter.submit(SETTINGS, t, "ACCEPTED", {**own, "tenant_id": t})
    ctx.accept({"settings": merged(own)})
