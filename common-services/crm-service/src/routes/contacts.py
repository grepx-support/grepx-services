# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_CONTACT - a person or a company (new, or changes to one)."""
from grepx_service import RequestContext

from domain import clean_contact
from domain.contacts import FIELDS
from dto import CONTACTS
from .common import mine, now_iso, plain, run, save


def handle(ctx: RequestContext) -> None:
    def body(t):
        key = ctx.text("contact_id")
        cur = mine(ctx, CONTACTS, key, t)
        if key and cur is None:
            raise ValueError("UNKNOWN_CONTACT")
        company = ctx.text("company_id")
        if company and mine(ctx, CONTACTS, company, t) is None:
            raise ValueError("UNKNOWN_CONTACT")
        fields = {k: ctx.get(k) for k in (*FIELDS, "tags") if ctx.get(k) is not None}
        row = {**clean_contact(fields, plain(cur, "contact_id") if cur else None), "tenant_id": t,
               "created_at": (cur or {}).get("created_at") or now_iso()}
        return {"contact": save(ctx, CONTACTS, key or None, row, "contact_id")}
    run(ctx, body)
