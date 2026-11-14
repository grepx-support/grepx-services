# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""END - the employee leaves: last working day and reason. The record stays for payroll and history."""
from datetime import date

from grepx_service import RequestContext

from domain.employee import day, text
from dto import ReasonCode
from .common import mine, plain, store, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    emp = mine(ctx, ctx.text("employee_id"), t)
    if emp is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    if emp.get("end_date"):
        return ctx.reject(ReasonCode.ALREADY_ENDED)
    try:
        last = day(ctx.get("end_date")) or date.today().isoformat()
    except ValueError as exc:
        return ctx.reject(str(exc))
    if emp.get("start_date") and last < emp["start_date"]:
        return ctx.reject(ReasonCode.INVALID_DATE)
    row = {**plain(emp), "end_date": last, "end_reason": text(ctx.get("reason"), 200), "active": last >= date.today().isoformat()}
    ctx.accept({"employee": store(ctx, emp["_key"], t, row)})
