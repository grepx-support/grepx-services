# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""LOGIN_CODE - the second step of a login: the 5-minute challenge from LOGIN (or a provider login) plus the
authenticator app's code, or one of the recovery codes. Right code -> the session; wrong -> refused."""
from grepx_auth import InvalidToken
from grepx_service import RequestContext

from dto import AuthField as F, ReasonCode
from .common import Deps, accept_session
from .two_step import spend


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    try:
        claims = deps.tokens.verify(deps.box.open(ctx.text(F.CHALLENGE_ENC)), kind="two_step")
    except (InvalidToken, ValueError):
        return ctx.reject(ReasonCode.CHALLENGE_EXPIRED)
    cred = deps.repo.by_id(str(claims.get("sub")))
    if cred is None or not cred.two_step:
        return ctx.reject(ReasonCode.CHALLENGE_EXPIRED)
    if not spend(cred, ctx.text(F.CODE)):
        return ctx.reject(ReasonCode.WRONG_CODE)
    deps.repo.save(cred)
    accept_session(ctx, cred, second_step_done=True, remember=bool(claims.get("remember")))
