# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TWO_STEP_STATUS - is two-step login on for this person, how many recovery codes are left, which providers are linked."""
from grepx_service import RequestContext

from dto import AuthField as F, ReasonCode
from .common import Deps


def handle(ctx: RequestContext) -> None:
    cred = Deps.get().repo.by_id(ctx.text(F.USER_ID))
    if cred is None:
        return ctx.reject(ReasonCode.UNKNOWN_USER)
    ctx.accept({"on": bool(cred.two_step), "recovery_left": len(cred.recovery), "linked": sorted(cred.external)})
