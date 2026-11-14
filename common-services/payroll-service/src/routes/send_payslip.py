# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND_PAYSLIP - send one person their payslip of a locked month by email / WhatsApp / SMS, with the PDF the caller
made attached (attachments=[{name, mime, data_b64, url}]). Each send is kept on the payslip (when, how, by whom).
The message is the deployment's template for the role "payslip" (values: org, name, month, net)."""
from grepx_service import RequestContext, notify, now_iso
from grepx_service.plugins import template_for

from domain.sending import can_send, reachable
from dto import EMPLOYEES, RUNS, SLIPS, ReasonCode
from .common import month_of, plain, tenant


def handle(ctx: RequestContext) -> None:
    t = tenant(ctx)
    month = t and month_of(ctx)
    if not month:
        return
    reason = can_send(ctx.read.accepted_one(RUNS, f"{t}:{month}"))
    if reason:
        return ctx.reject(reason)
    eid = ctx.text("employee_id")
    slip, person = ctx.read.accepted_one(SLIPS, f"{t}:{month}:{eid}"), ctx.read.accepted_one(EMPLOYEES, eid)
    if slip is None or person is None or person.get("tenant_id") != t:
        return ctx.reject(ReasonCode.UNKNOWN_EMPLOYEE)
    try:
        channels = reachable(ctx.get("channels") or [], person.get("email", ""), person.get("phone", ""))
    except ValueError as exc:
        return ctx.reject(str(exc))
    sent = list(slip.get("sent") or [])
    notify(ctx.emitter, template_for(ctx.emitter.cfg, "payslip"), email=person.get("email", ""), phone=person.get("phone", ""),
           channels=channels, ref=f"payslip-{t}-{month}-{eid}-{len(sent)}", tenant_id=t, auto=False,
           attachments=[a for a in ctx.get("attachments") or [] if isinstance(a, dict)] or None,
           values={"name": slip.get("name", ""), "month": month, "net": f"{slip.get('net', 0):,.2f}", "org": ctx.text("org")})
    sent.append({"at": now_iso(), "channels": channels, "by": ctx.text("actor_name")})
    saved = {**plain(slip), "sent": sent}
    ctx.emitter.submit(SLIPS, slip["_key"], "ACCEPTED", saved)
    ctx.accept({"payslip": saved})
