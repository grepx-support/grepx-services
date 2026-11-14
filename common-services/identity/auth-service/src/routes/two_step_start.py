# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TWO_STEP_START - a new authenticator key for the signed-in person; nothing changes until a first code matches."""
from grepx_service import RequestContext

from domain import totp
from dto import AuthField as F, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_id(ctx.text(F.USER_ID))
    if cred is None:
        return ctx.reject(ReasonCode.UNKNOWN_USER)
    secret = totp.new_secret()
    cred.two_step_pending = deps.box.seal(secret)
    deps.repo.save(cred)
    link = totp.app_link(secret, cred.email, ctx.text(F.ISSUER) or "GrepX")
    ctx.accept({F.SECRET_ENC: deps.box.seal(secret), F.APP_LINK_ENC: deps.box.seal(link)})
