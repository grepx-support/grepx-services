# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_TYPE - add or change a leave type of the business (same type_id = change it; active false = switched off)."""
from grepx_service import RequestContext

from domain import clean_type
from dto import TYPES
from .common import tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    try:
        kind = clean_type(ctx.fields)
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.emitter.submit(TYPES, f"{t}:{kind['type_id']}", "ACCEPTED", {**kind, "tenant_id": t})
    ctx.accept({"type": kind})
