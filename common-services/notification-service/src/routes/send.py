# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND — check template + admin settings, render, deliver; record SENT / LOGGED / FAILED / SKIPPED."""

import grepx_contracts as gc
from grepx_config.deployment import org_name
from grepx_service import CircuitOpen, RequestContext, Resilient, now_iso

from channels import ChannelFactory
from domain import render
from dto import SETTINGS_TABLE, TEMPLATES_TABLE, Delivery, NotificationField as F, ReasonCode


class Deps:
    channels = ChannelFactory()
    guards: dict[str, Resilient] = {}

    @classmethod
    def guard(cls, name: str) -> Resilient:
        """One circuit breaker + retry + bulkhead per external channel."""
        return cls.guards.setdefault(name, Resilient(f"channel-{name}", attempts=2, failure_threshold=5, reset_seconds=60))


def integration_settings(ctx: RequestContext) -> dict:
    """Admin-saved delivery settings (settings-service), sealed secrets opened with the platform key."""
    from grepx_auth import open_settings
    return open_settings(ctx.read.accepted(gc.settings.APP_SETTINGS))


def handle(ctx: RequestContext) -> None:
    template = ctx.read.accepted_one(TEMPLATES_TABLE, ctx.text(F.TEMPLATE))
    if template is None:
        return ctx.reject(ReasonCode.UNKNOWN_TEMPLATE)
    recipient, channel_name = ctx.text(F.RECIPIENT), ctx.text(F.CHANNEL)
    if not recipient:
        return ctx.reject(ReasonCode.MISSING_RECIPIENT)
    settings = ctx.read.accepted_one(SETTINGS_TABLE, ctx.text(F.TEMPLATE))
    allowed = (settings or {}).get("channels") or template.get("channels") or []
    if ctx.get(F.AUTO, True) and ((settings and settings.get("enabled") is False) or channel_name not in allowed):
        return ctx.accept({F.DELIVERY: Delivery.SKIPPED})
    values = {"org": org_name(), **dict(ctx.get(F.VALUES, {}))}
    message = render(template, settings, channel_name, values, values["org"])
    channel, real = Deps.channels.get(channel_name, integration_settings(ctx))
    try:
        Deps.guard(channel.name).call(lambda: channel.send(recipient, message.subject, message.body, message.html))
        delivery, error = (Delivery.SENT if real else Delivery.LOGGED), ""
    except CircuitOpen:
        delivery, error = Delivery.FAILED, f"{channel.name} temporarily unavailable (circuit open)"
    except Exception as exc:  # delivery problems are recorded, never crash the service
        delivery, error = Delivery.FAILED, str(exc)[:200]
    ctx.accept({F.SUBJECT: message.subject, F.BODY: message.body, F.DELIVERY: delivery, F.ERROR: error, F.SENT_AT: now_iso()})
