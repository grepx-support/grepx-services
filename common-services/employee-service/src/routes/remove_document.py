# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REMOVE_DOCUMENT - take one document off an employee."""
from grepx_service import RequestContext

from dto import ReasonCode
from .common import mine, plain, store, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    emp = mine(ctx, ctx.text("employee_id"), t)
    if emp is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    docs = [d for d in emp.get("documents") or [] if d.get("doc_id") != ctx.text("doc_id")]
    ctx.accept({"employee": store(ctx, emp["_key"], t, {**plain(emp), "documents": docs})})
