# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE - add or change an employee. An email is used by one current employee of the business at a time."""
from grepx_service import RequestContext, new_key

from domain import clean_employee
from dto import EMPLOYEES, ReasonCode
from .common import mine, plain, store, tenant

FIELDS = ("name", "email", "phone", "position", "department", "home_site", "sites", "start_date", "end_date", "pay", "user_id",
          "emergency", "notes")


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    employee_id = ctx.text("employee_id")
    current = mine(ctx, employee_id, t)
    if employee_id and current is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    try:
        row = clean_employee({f: ctx.get(f) for f in FIELDS}, plain(current) if current else None)
    except ValueError as exc:
        return ctx.reject(str(exc))
    employee_id = employee_id or new_key()[:12]
    if row["email"] and any(e["_key"] != employee_id and e.get("email") == row["email"] and e.get("active", True)
                            for e in ctx.read.accepted(EMPLOYEES, tenant_id=t)):
        return ctx.reject(ReasonCode.DUPLICATE_EMAIL)
    ctx.accept({"employee": store(ctx, employee_id, t, row)})
