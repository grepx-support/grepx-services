# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TEST_CHANNEL — sign in to a delivery channel (email / sms / whatsapp) with the saved settings; nothing is sent."""
from grepx_service import RequestContext

from dto import NotificationField as F, ReasonCode
from .send import Deps, integration_settings


def handle(ctx: RequestContext) -> None:
    channel, real = Deps.channels.get(ctx.text(F.CHANNEL), integration_settings(ctx))
    if not real:
        return ctx.reject(ReasonCode.NOT_CONFIGURED)
    try:
        message = channel.check()
    except Exception as exc:  # the provider's own words are the useful part
        return ctx.reject(ReasonCode.CHECK_FAILED, detail=str(exc)[:300])
    ctx.accept({"message": message})
