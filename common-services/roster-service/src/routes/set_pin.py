# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_PIN - the person's 4 to 6 digit clock PIN; only a salted hash is kept."""
import hashlib

from grepx_service import RequestContext

from dto import PINS, ReasonCode
from .common import employee, tenant


def digest(t: str, employee_id: str, pin: str) -> str:
    return hashlib.sha256(f"{t}:{employee_id}:{pin}".encode()).hexdigest()


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    if t is None:
        return
    eid, pin = ctx.text("employee_id"), ctx.text("pin")
    if employee(ctx, t, eid) is None:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    if not (pin.isdigit() and 4 <= len(pin) <= 6):
        return ctx.reject(ReasonCode.INVALID_PIN)
    ctx.emitter.submit(PINS, f"{t}:{eid}", "ACCEPTED", {"tenant_id": t, "employee_id": eid, "hash": digest(t, eid, pin)})
    ctx.accept({"pin": "", "employee_id": eid})
