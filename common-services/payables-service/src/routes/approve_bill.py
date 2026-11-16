# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""APPROVE_BILL - ok to pay. A bill that does not match its order needs a note. Unless told not to (recost false), each
item's cost becomes what it really cost on this bill, landed costs included (item-service SET_COSTS)."""
from grepx_service import RequestContext

from domain import approve
from domain.landed import new_costs
from .common import run, set_costs


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = approve(ap.bill(ctx.text("bill_id")), ctx.text("note"), ctx.text("approved_by") or ctx.text("actor_name"))   # approved_by: decided in approval-service
        costs = new_costs(bill) if bill.get("recost", True) else {}
        recosted = costs if set_costs(ctx, ap.tenant, bill, costs) else {}
        return {"bill": ap.save(bill["bill_id"], bill), "recosted": recosted}
    run(ctx, body)
