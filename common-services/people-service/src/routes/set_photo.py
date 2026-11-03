# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_PHOTO — link (or clear) the person's processed avatar from media-service."""
from grepx_service import RequestContext

from dto import PersonField as F, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    person = load(ctx, ctx.text(F.PERSON_ID))
    if person is None:
        return ctx.reject(ReasonCode.UNKNOWN_PERSON)
    save(ctx, {**person, F.PHOTO_ID.value: ctx.text(F.PHOTO_ID)})
