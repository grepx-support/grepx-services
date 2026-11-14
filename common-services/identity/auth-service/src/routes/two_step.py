# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Shared by the two-step routes: check a code (app code first, else a recovery code) and spend it."""
import time

from domain import recovery, totp
from .common import Deps


def spend(cred, code: str, now: float | None = None) -> bool:
    """True when the code is right; the code (or recovery code) cannot be used again."""
    secret = Deps.get().box.open(cred.two_step)
    step = totp.matching_step(secret, code, time.time() if now is None else now, cred.last_step)
    if step is not None:
        cred.last_step = step
        return True
    left = recovery.use(code, cred.recovery)
    if left is None:
        return False
    cred.recovery = left
    return True
