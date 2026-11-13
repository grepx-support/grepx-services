# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND — check template + admin settings, render, deliver (with any files attached); record SENT / LOGGED / FAILED / SKIPPED."""

import base64

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


def settings_for(ctx: RequestContext, template: str) -> dict | None:
    """The business's own choice for this message first ("<tenant>:<template>"), else the platform default."""
    tenant = ctx.text(F.TENANT_ID)
    own = ctx.read.accepted_one(SETTINGS_TABLE, f"{tenant}:{template}") if tenant else None
    return own or ctx.read.accepted_one(SETTINGS_TABLE, template)


MAX_ATTACHED = 8 * 1024 * 1024


def attachments(raw: list) -> list[dict] | None:
    """[{name, mime, data_b64}] -> [{name, mime, data}]; None when together they are over 8 MB."""
    files = [{"name": str(a.get("name") or "file")[:120], "mime": str(a.get("mime") or "application/octet-stream"),
              "data": base64.b64decode(a.get("data_b64") or "")} for a in raw if isinstance(a, dict)]
    return None if sum(len(f["data"]) for f in files) > MAX_ATTACHED else files


def handle(ctx: RequestContext) -> None:
    template = ctx.read.accepted_one(TEMPLATES_TABLE, ctx.text(F.TEMPLATE))
    if template is None:
        return ctx.reject(ReasonCode.UNKNOWN_TEMPLATE)
    recipient, channel_name = ctx.text(F.RECIPIENT), ctx.text(F.CHANNEL)
    if not recipient:
        return ctx.reject(ReasonCode.MISSING_RECIPIENT)
    settings = settings_for(ctx, ctx.text(F.TEMPLATE))
    allowed = (settings or {}).get("channels") or template.get("channels") or []
    if ctx.get(F.AUTO, True) and ((settings and settings.get("enabled") is False) or channel_name not in allowed):
        return ctx.accept({F.DELIVERY: Delivery.SKIPPED})
    values = {"org": org_name(), **dict(ctx.get(F.VALUES, {}))}
    message = render(template, settings, channel_name, values, values["org"])
    files = attachments(ctx.get(F.ATTACHMENTS) or [])
    if files is None:
        return ctx.reject(ReasonCode.ATTACHMENT_TOO_LARGE)
    channel, real = Deps.channels.get(channel_name, integration_settings(ctx))
    extra = {"attachments": files} if files else {}
    try:
        Deps.guard(channel.name).call(lambda: channel.send(recipient, message.subject, message.body, message.html, **extra))
        delivery, error = (Delivery.SENT if real else Delivery.LOGGED), ""
    except CircuitOpen:
        delivery, error = Delivery.FAILED, f"{channel.name} temporarily unavailable (circuit open)"
    except Exception as exc:  # delivery problems are recorded, never crash the service
        delivery, error = Delivery.FAILED, str(exc)[:200]
    ctx.accept({F.SUBJECT: message.subject, F.BODY: message.body, F.DELIVERY: delivery, F.ERROR: error, F.SENT_AT: now_iso(),
                F.ATTEMPT: int(ctx.get(F.ATTEMPT) or 1)})
