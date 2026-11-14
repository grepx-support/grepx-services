# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TWO_STEP_ENABLE - the first code from the app matches the new key: two-step login is on. The ten recovery codes
are given back once (sealed); only their hashes are kept."""
import json
import time

from grepx_service import RequestContext

from domain import recovery, totp
from dto import AuthField as F, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_id(ctx.text(F.USER_ID))
    if cred is None or not cred.two_step_pending:
        return ctx.reject(ReasonCode.NOT_STARTED)
    step = totp.matching_step(deps.box.open(cred.two_step_pending), ctx.text(F.CODE), time.time())
    if step is None:
        return ctx.reject(ReasonCode.WRONG_CODE)
    codes = recovery.new_codes()
    cred.two_step, cred.two_step_pending, cred.last_step = cred.two_step_pending, "", step
    cred.recovery = [recovery.digest(c) for c in codes]
    deps.repo.save(cred)
    ctx.accept({F.CODE: "", F.RECOVERY_ENC: deps.box.seal(json.dumps(codes))})
