# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TWO_STEP_DISABLE - switch two-step login off: the password and a current code (or a recovery code) are needed.
An operator can also switch it off for someone who lost their phone (by_admin: no password or code needed)."""
from grepx_auth import verify_password
from grepx_service import RequestContext

from dto import AuthField as F, ReasonCode
from .common import Deps
from .two_step import spend


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_id(ctx.text(F.USER_ID))
    if cred is None or not cred.two_step:
        return ctx.reject(ReasonCode.NOT_STARTED)
    if not ctx.get("by_admin"):
        if not verify_password(deps.box.open(ctx.text(F.PASSWORD_ENC)), cred.password_hash):
            return ctx.reject(ReasonCode.INVALID_CREDENTIALS)
        if not spend(cred, ctx.text(F.CODE)):
            return ctx.reject(ReasonCode.WRONG_CODE)
    cred.two_step, cred.recovery, cred.two_step_pending = "", [], ""
    deps.repo.save(cred)
    ctx.accept({F.PASSWORD_ENC: "", F.CODE: ""})
