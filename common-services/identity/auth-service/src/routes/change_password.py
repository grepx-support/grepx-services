# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CHANGE_PASSWORD — the signed-in user changes their own password (current one optional for admins' flows)."""
from grepx_auth import hash_password, verify_password
from grepx_service import RequestContext

from domain import MIN_PASSWORD
from dto import AuthField, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_id(ctx.text(AuthField.USER_ID))
    if cred is None:
        return ctx.reject(ReasonCode.UNKNOWN_USER)
    current = ctx.text(AuthField.CURRENT_ENC)
    if current and not verify_password(deps.box.open(current), cred.password_hash):
        return ctx.reject(ReasonCode.INVALID_CREDENTIALS)
    password = deps.box.open(ctx.text(AuthField.PASSWORD_ENC))
    if len(password) < MIN_PASSWORD:
        return ctx.reject(ReasonCode.WEAK_PASSWORD)
    cred.password_hash = hash_password(password)
    deps.repo.save(cred)
    ctx.accept({AuthField.PASSWORD_ENC: "", AuthField.CURRENT_ENC: ""})
