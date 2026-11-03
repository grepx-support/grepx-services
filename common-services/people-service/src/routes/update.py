# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""UPDATE — change profile fields (partial). Email stays unique."""
from grepx_service import RequestContext

from domain import ProfileError
from dto import PersonField as F, ReasonCode
from .common import clean, editable, email_owner, load, save


def handle(ctx: RequestContext) -> None:
    person = load(ctx, ctx.text(F.PERSON_ID))
    if person is None:
        return ctx.reject(ReasonCode.UNKNOWN_PERSON)
    try:
        changes = clean(ctx, {k: ctx.fields[k] for k in editable(ctx) if k in ctx.fields}, partial=True)
    except ProfileError as exc:
        return ctx.reject(str(exc))
    owner = email_owner(ctx, changes["email"]) if "email" in changes else None
    if owner and owner != person[F.PERSON_ID.value]:
        return ctx.reject(ReasonCode.EMAIL_TAKEN)
    save(ctx, {**person, **changes})
