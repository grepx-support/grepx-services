# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RESET_CONFIRM — set a new password from a valid reset token (token dies once the password changes)."""
from grepx_auth import InvalidToken, hash_password
from grepx_service import RequestContext

from domain import MIN_PASSWORD, fingerprint
from dto import AuthField, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    try:
        claims = deps.tokens.verify(deps.box.open(ctx.text(AuthField.TOKEN_ENC)), kind="reset")
    except InvalidToken:
        return ctx.reject(ReasonCode.INVALID_TOKEN)
    cred = deps.repo.by_id(str(claims.get("sub")))
    if cred is None or claims.get("fp") != fingerprint(cred.password_hash):
        return ctx.reject(ReasonCode.INVALID_TOKEN)
    password = deps.box.open(ctx.text(AuthField.PASSWORD_ENC))
    if len(password) < MIN_PASSWORD:
        return ctx.reject(ReasonCode.WEAK_PASSWORD)
    cred.password_hash = hash_password(password)
    deps.repo.save(cred)
    ctx.accept({AuthField.PASSWORD_ENC: "", AuthField.TOKEN_ENC: "", AuthField.USER_ID: cred.user_id})
