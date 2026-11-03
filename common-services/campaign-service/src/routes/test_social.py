# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TEST_SOCIAL — read the social account with the saved credentials (nothing is posted)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from social import SOCIAL
from social import settings as social_settings


def handle(ctx: RequestContext) -> None:
    channel = SOCIAL.get(ctx.text("network"))
    if channel is None:
        return ctx.reject("UNKNOWN_NETWORK")
    social_settings.load(ctx.read.accepted(gc.settings.APP_SETTINGS))
    if not channel.configured():
        return ctx.reject("NOT_CONFIGURED")
    try:
        message = channel.check()
    except Exception as exc:  # the network's own words are the useful part
        return ctx.reject("CHECK_FAILED", detail=str(exc)[:300])
    ctx.accept({"message": message})
