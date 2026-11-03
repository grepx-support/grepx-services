# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET — store one setting. Secrets arrive already sealed by the sender (platform SecretBox) and are stored as is,
so only services holding the platform key can read them; nothing is ever logged in clear."""
from grepx_service import RequestContext, now_iso

from domain import MAX_VALUE, valid_name
from grepx_auth import is_sealed

from dto import SETTINGS_TABLE


def handle(ctx: RequestContext) -> None:
    name, value = ctx.text("name"), str(ctx.get("value", "") or "")
    if not valid_name(name):
        return ctx.reject("INVALID_NAME")
    if len(value) > MAX_VALUE:
        return ctx.reject("TOO_LONG")
    secret = bool(ctx.get("secret", False)) or is_sealed(value)
    ctx.emitter.submit(SETTINGS_TABLE, name, "ACCEPTED", {"name": name, "value": value, "secret": secret,
                                                          "updated_by": ctx.text("actor_id"), "updated_at": now_iso()})
    ctx.accept({"name": name, "value": "", "secret": secret})
