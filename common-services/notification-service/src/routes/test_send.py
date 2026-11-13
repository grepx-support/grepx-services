# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TEST_SEND - send a short test message on one channel to one address, with the saved settings (Integrations page).
Without a provider it is only logged, and says so."""
from grepx_config.deployment import org_name
from grepx_service import RequestContext, now_iso

from dto import Delivery, NotificationField as F, ReasonCode
from .send import Deps, integration_settings

CHANNELS = ("email", "sms", "whatsapp")


def handle(ctx: RequestContext) -> None:
    name, recipient = ctx.text(F.CHANNEL), ctx.text(F.RECIPIENT)
    if name not in CHANNELS:
        return ctx.reject(ReasonCode.UNKNOWN_CHANNEL)
    if not recipient:
        return ctx.reject(ReasonCode.MISSING_RECIPIENT)
    channel, real = Deps.channels.get(name, integration_settings(ctx))
    subject = f"Test message from {org_name()}"
    body = f"This is a test from {org_name()}: your {name} channel works."
    try:
        channel.send(recipient, subject, body, None)
    except Exception as exc:  # the provider's words help the person fix the setting
        return ctx.accept({F.DELIVERY: Delivery.FAILED, F.ERROR: str(exc)[:300], F.SENT_AT: now_iso()})
    ctx.accept({F.DELIVERY: Delivery.SENT if real else Delivery.LOGGED, F.ERROR: "", F.SENT_AT: now_iso()})
