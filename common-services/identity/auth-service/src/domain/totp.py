# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Two-step login with an authenticator app (Google Authenticator, Microsoft Authenticator, Authy...): time-based
six-digit codes (RFC 6238, 30-second steps, one step of clock drift allowed), each code usable once."""
import base64
import hashlib
import hmac
import secrets
import struct
from urllib.parse import quote

STEP_SECONDS = 30
DRIFT = 1


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def code_at(secret: str, step: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    at = digest[-1] & 0x0F
    return f"{(struct.unpack('>I', digest[at:at + 4])[0] & 0x7FFFFFFF) % 1_000_000:06d}"


def matching_step(secret: str, code: str, now: float, last_step: int = 0) -> int | None:
    """The time step the code belongs to, or None (wrong, too old, or already used: steps up to last_step are spent)."""
    code = "".join(c for c in str(code) if c.isdigit())
    if len(code) != 6:
        return None
    here = int(now // STEP_SECONDS)
    for step in range(here - DRIFT, here + DRIFT + 1):
        if step > last_step and hmac.compare_digest(code_at(secret, step), code):
            return step
    return None


def app_link(secret: str, email: str, issuer: str) -> str:
    """What the authenticator app reads from the QR code (or a tap on a phone)."""
    return f"otpauth://totp/{quote(issuer)}:{quote(email)}?secret={secret}&issuer={quote(issuer)}&digits=6&period={STEP_SECONDS}"
