# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEED_TEMPLATE — a product registers a checklist (e.g. the 28-step blood-drive playbook)."""
from grepx_service import RequestContext

from dto import TEMPLATES_TABLE, ChecklistField as F, ReasonCode


def handle(ctx: RequestContext) -> None:
    key, items = ctx.text(F.TEMPLATE_KEY), list(ctx.get(F.ITEMS, []))
    if not key or not items:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    ctx.emitter.submit(TEMPLATES_TABLE, key, "ACCEPTED", {F.TEMPLATE_KEY.value: key, F.NAME.value: ctx.text(F.NAME) or key, F.ITEMS.value: items})
