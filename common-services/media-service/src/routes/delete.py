# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DELETE — remove an image file and its record."""
from grepx_service import RequestContext

from dto import MEDIA_TABLE, MediaField as F, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    media = ctx.read.accepted_one(MEDIA_TABLE, ctx.text(F.MEDIA_ID))
    if media is None:
        return ctx.reject(ReasonCode.UNKNOWN_MEDIA)
    Deps.store().delete(media[F.KEY.value])
    ctx.emitter.submit(MEDIA_TABLE, media["_key"], "DELETED", {F.MEDIA_ID.value: media["_key"]})
