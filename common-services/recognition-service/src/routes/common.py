# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Issue certificates and vouchers for a completed event (idempotent per person + event)."""

from grepx_service import Emitter, Reader, notify
from grepx_service.plugins import template_for

from domain import allocate, certificate_code
from dto import CERTIFICATES_TABLE, BOOKINGS_TABLE, VOUCHERS_TABLE
from grepx_config.deployment import link


def issue(emitter: Emitter, read: Reader, event: dict, offer: dict) -> dict:
    attendees = sorted((r for r in read.accepted(BOOKINGS_TABLE, event_id=event["_key"]) if r.get("state") == "attended"),
                    key=lambda r: r["_key"])
    need = [r for r in attendees if not read.accepted_one(VOUCHERS_TABLE, f"{event['_key']}-{r['person_id']}")] if offer.get("title") else []
    codes = allocate(offer, [r["person_id"] for r in need])
    certificates = 0
    for reg in attendees:
        code = certificate_code(reg["person_id"], event["_key"])
        new_certificate = not read.accepted_one(CERTIFICATES_TABLE, code)
        if new_certificate:
            emitter.submit(CERTIFICATES_TABLE, code, "ACCEPTED", {"code": code, "person_id": reg["person_id"], "event_id": event["_key"],
                                                                   "name": reg.get("name", ""), "event_title": event.get("title", ""),
                                                                   "attended_on": event.get("event_date", "")})
            certificates += 1
        voucher = ""
        if reg["person_id"] in codes:
            emitter.submit(VOUCHERS_TABLE, f"{event['_key']}-{reg['person_id']}", "ACCEPTED", {
                "person_id": reg["person_id"], "event_id": event["_key"], "event_title": event.get("title", ""), "title": offer["title"],
                "partner": offer.get("partner", ""), "details": offer.get("details", ""), "code": codes[reg["person_id"]],
                "expires_on": offer.get("expires_on", "")})
            voucher = f"🎁 {offer['title']}" + (f" — code {codes[reg['person_id']]}" if codes[reg["person_id"]] else "")
        if not new_certificate and not voucher:
            continue
        notify(emitter, template_for(emitter.cfg, "certificate"), email=reg.get("email", ""), phone=reg.get("phone", ""), ref=f"cert-{code}-{bool(voucher)}",
               values={"first_name": reg.get("name", "").split(" ")[0], "event_title": event.get("title", ""),
                       "link": link(emitter.cfg, "certificate", code=code), "voucher": voucher}, user_id=reg["person_id"])
    return {"certificates": certificates, "vouchers": len(codes), "vouchers_short": len(need) - len(codes)}
