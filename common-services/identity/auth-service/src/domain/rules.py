# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Pure auth rules."""
import hashlib

MIN_PASSWORD = 8
RESET_HOURS = 1
RESET_COOLDOWN_SECONDS = 60
STAFF_HOURS = 12
REMEMBER_HOURS = 24 * 7


def session_hours(is_staff: bool, remember: bool) -> int:
    """Remember-me is for members only; staff sessions are always short."""
    return REMEMBER_HOURS if remember and not is_staff else STAFF_HOURS


def fingerprint(password_hash: str) -> str:
    """Changes whenever the password changes, so a reset link works once."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]
