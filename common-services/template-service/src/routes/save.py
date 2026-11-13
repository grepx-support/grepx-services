# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE — settings for one automatic message: on/off, channels, optional custom wording; for the platform or one business."""
from grepx_service import RequestContext

from domain import placeholders_in, settings_key
from dto import CHANNELS, SETTINGS_TABLE, TEMPLATES_TABLE, ReasonCode, TemplateField as F


def handle(ctx: RequestContext) -> None:
    key = ctx.text(F.TEMPLATE_KEY)
    template = ctx.read.accepted_one(TEMPLATES_TABLE, key)
    if template is None:
        return ctx.reject(ReasonCode.UNKNOWN_TEMPLATE)
    channels = list(ctx.get(F.CHANNELS, template.get(F.CHANNELS.value, [])))
    if any(c not in CHANNELS for c in channels):
        return ctx.reject(ReasonCode.UNKNOWN_CHANNEL)
    subject, text = ctx.text(F.SUBJECT), str(ctx.get(F.TEXT, "") or "")
    unknown = placeholders_in(subject, text) - set(template.get(F.PLACEHOLDERS.value) or [])
    if unknown:
        return ctx.reject(ReasonCode.UNKNOWN_PLACEHOLDER, ", ".join(sorted(unknown)))
    tenant = ctx.text(F.FOR_TENANT)
    ctx.emitter.submit(SETTINGS_TABLE, settings_key(key, tenant), "ACCEPTED", {F.TEMPLATE_KEY.value: key, F.FOR_TENANT.value: tenant, F.ENABLED.value: bool(ctx.get(F.ENABLED, True)),
                                                         F.CHANNELS.value: channels, F.SUBJECT.value: subject, F.TEXT.value: text})
