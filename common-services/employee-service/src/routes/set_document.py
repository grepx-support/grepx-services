# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_DOCUMENT - add or change one document of an employee (same doc_id = change it)."""
from grepx_service import RequestContext, new_key

from domain import clean_document
from dto import ReasonCode
from .common import mine, plain, store, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    emp = mine(ctx, ctx.text("employee_id"), t)
    if emp is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    try:
        doc = clean_document(ctx.get("document") or {})
    except ValueError as exc:
        return ctx.reject(str(exc))
    doc["doc_id"] = doc["doc_id"] or new_key()[:10]
    docs = [d for d in emp.get("documents") or [] if d.get("doc_id") != doc["doc_id"]] + [doc]
    ctx.accept({"employee": store(ctx, emp["_key"], t, {**plain(emp), "documents": docs})})
