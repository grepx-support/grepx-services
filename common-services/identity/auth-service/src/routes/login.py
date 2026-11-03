# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""LOGIN — verify credentials, issue a sealed access token carrying role and tenant."""
from grepx_auth import verify_password
from grepx_service import RequestContext

from dto import AuthField, ReasonCode
from .common import Deps, accept_session


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_email(ctx.text(AuthField.EMAIL))
    password = deps.box.open(ctx.text(AuthField.PASSWORD_ENC))
    if cred is None or not verify_password(password, cred.password_hash):
        return ctx.reject(ReasonCode.INVALID_CREDENTIALS)
    accept_session(ctx, cred)
