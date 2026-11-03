"""Contact validation every product shares: name, email, phone (country rules from config `phone:`). Pure."""
from __future__ import annotations

import re
import secrets

from grepx_common import Phone, PhoneError

NAME_MAX = 100
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PLACEHOLDER_DOMAIN = "no-email.local"


class ProfileError(ValueError):
    """str(e) is the reason code."""


def placeholder_email() -> str:
    return f"walkin-{secrets.token_hex(4)}@{PLACEHOLDER_DOMAIN}"


def clean_contact(raw: dict, *, partial: bool = False) -> dict:
    """Raises ProfileError(<REASON_CODE>). partial=True validates only the keys present."""
    out = {}
    has = lambda k: k in raw and raw[k] not in (None, "")  # noqa: E731
    if has("name") or not partial:
        name = str(raw.get("name") or "").strip()
        if len(name) < 2 or len(name) > NAME_MAX or any(c.isdigit() for c in name):
            raise ProfileError("INVALID_NAME")
        out["name"] = name
    if has("email") or not partial:
        email = str(raw.get("email") or "").strip().lower()
        if not EMAIL.match(email):
            raise ProfileError("INVALID_EMAIL")
        out["email"] = email
    if has("phone") or not partial:
        try:
            out["phone"] = Phone.normalize(str(raw.get("phone") or ""))
        except PhoneError as exc:
            raise ProfileError("INVALID_PHONE") from exc
    return out
