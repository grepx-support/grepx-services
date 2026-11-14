# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Recovery codes: ten one-time codes shown once when two-step login is switched on, for a lost phone.
Only their hashes are kept; each works once."""
import hashlib
import secrets

COUNT = 10


def _norm(code: str) -> str:
    return "".join(c for c in str(code).lower() if c.isalnum())


def digest(code: str) -> str:
    return hashlib.sha256(_norm(code).encode()).hexdigest()


def new_codes() -> list[str]:
    return [f"{secrets.token_hex(2)}-{secrets.token_hex(2)}" for _ in range(COUNT)]


def use(code: str, hashes: list[str]) -> list[str] | None:
    """The hashes left after using this code, or None when it is not one of them."""
    d = digest(code)
    return [h for h in hashes if h != d] if _norm(code) and d in hashes else None
