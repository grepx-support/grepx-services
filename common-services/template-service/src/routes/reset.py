# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RESET — drop custom wording and channel choices; built-in design applies again."""
from grepx_service import RequestContext

from domain import settings_key
from dto import SETTINGS_TABLE, TemplateField as F


def handle(ctx: RequestContext) -> None:
    key, tenant = ctx.text(F.TEMPLATE_KEY), ctx.text(F.FOR_TENANT)
    ctx.emitter.submit(SETTINGS_TABLE, settings_key(key, tenant), "DELETED", {F.TEMPLATE_KEY.value: key, F.FOR_TENANT.value: tenant})
