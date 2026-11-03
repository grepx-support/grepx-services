# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEED — a product registers a built-in template (label, placeholders, per-channel bodies)."""
from grepx_service import RequestContext

from dto import TEMPLATES_TABLE, ReasonCode, TemplateField as F


def handle(ctx: RequestContext) -> None:
    key = ctx.text(F.TEMPLATE_KEY)
    if not key or not ctx.get(F.BODIES):
        return ctx.reject(ReasonCode.MISSING_FIELD)
    ctx.emitter.submit(TEMPLATES_TABLE, key, "ACCEPTED", {
        F.TEMPLATE_KEY.value: key, F.LABEL.value: ctx.text(F.LABEL) or key, F.PLACEHOLDERS.value: list(ctx.get(F.PLACEHOLDERS, [])),
        F.BODIES.value: dict(ctx.get(F.BODIES)), F.CHANNELS.value: list(ctx.get(F.CHANNELS, ["email", "whatsapp"]))})
