# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DELETE — remove a setting (readers fall back to the default / .env value)."""
from grepx_service import RequestContext

from dto import SETTINGS_TABLE


def handle(ctx: RequestContext) -> None:
    name = ctx.text("name")
    if ctx.read.accepted_one(SETTINGS_TABLE, name):
        ctx.emitter.submit(SETTINGS_TABLE, name, "DELETED", {"name": name})
    ctx.accept({"name": name})
