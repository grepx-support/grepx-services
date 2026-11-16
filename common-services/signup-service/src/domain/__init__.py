# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a usable sign-up looks like, short names, codes and how long things last (no I/O)."""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")
SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28}[a-z0-9])$")      # 3-30: letters, digits, inner hyphens
# Names that are, or will be, the platform's own addresses (www.<domain>, api.<domain>, /b/admin ...).
RESERVED = frozenset("""
www app api admin administrator platform login signin signup register account accounts auth help support
status docs blog mail email smtp ftp static assets cdn media files dev test staging demo grafana metrics
health billing pay payments root system owner operator grepx
""".split())

HOLD_HOURS = 24           # a short name stays held for an unfinished sign-up this long; the email link works as long
CODE_MINUTES = 15         # a phone code works this long
MAX_TRIES = 5             # wrong phone codes before a new one must be sent
RESEND_SECONDS = 60       # at most one new link / code a minute


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def at(iso: str) -> datetime:
    try:
        value = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def later(now: datetime, *, hours: float = 0, minutes: float = 0, seconds: float = 0) -> str:
    return iso(now + timedelta(hours=hours, minutes=minutes, seconds=seconds))


def _text(value, n: int) -> str:
    return " ".join(str(value or "").split())[:n]


def suggest_slug(name: str) -> str:
    """A short name from the business name: 'Galaxy Mobiles & Laptops' -> 'galaxy-mobiles-and-laptops' (at most 30)."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower().replace("&", " and ")).strip("-")
    return s[:30].rstrip("-")


def slug_problem(slug: str) -> str:
    """'' when the short name is well formed and not reserved, else the reason."""
    if not SLUG.match(slug or "") or "--" in slug:
        return "INVALID_SLUG"
    return "RESERVED_SLUG" if slug in RESERVED else ""


def clean_phone(raw: str) -> str:
    """'+91 98450 12345' -> '+919845012345'; '' when it is not 8-15 digits."""
    digits = re.sub(r"\D", "", str(raw or ""))
    return f"+{digits}" if 8 <= len(digits) <= 15 else ""


def clean_signup(raw: dict) -> dict:
    """The owner's details, cleaned. Raises ValueError(reason). A filled hidden 'website' field means a bot (SPAM)."""
    if raw.get("website"):
        raise ValueError("SPAM")
    business = _text(raw.get("business_name"), 80)
    if len(business) < 2:
        raise ValueError("INVALID_BUSINESS_NAME")
    slug = str(raw.get("slug") or "").strip().lower() or suggest_slug(business)
    problem = slug_problem(slug)
    if problem:
        raise ValueError(problem)
    owner = _text(raw.get("owner_name"), 80)
    if len(owner) < 2:
        raise ValueError("INVALID_NAME")
    email = _text(raw.get("email"), 200).lower()
    if not EMAIL.match(email):
        raise ValueError("INVALID_EMAIL")
    phone = clean_phone(raw.get("phone"))
    if not phone:
        raise ValueError("INVALID_PHONE")
    currency = _text(raw.get("currency"), 3).upper()
    if currency and not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("INVALID_CURRENCY")
    if not str(raw.get("password_enc") or ""):
        raise ValueError("MISSING_PASSWORD")
    return {"business_name": business, "slug": slug, "owner_name": owner, "email": email, "phone": phone, "currency": currency,
            "timezone": _text(raw.get("timezone"), 64), "product": _text(raw.get("product"), 40)}


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_token() -> str:
    return secrets.token_urlsafe(24)


def digest(secret: str, salt: str) -> str:
    """Only hashes of the code and the link token are kept (salted with the sign-up id)."""
    return hashlib.sha256(f"{salt}:{str(secret or '').strip()}".encode()).hexdigest()


def masked_phone(phone: str) -> str:
    return phone[:3] + "*" * max(len(phone) - 6, 0) + phone[-3:] if len(phone) > 6 else phone


def masked_email(email: str) -> str:
    name, _, host = email.partition("@")
    return f"{name[:2]}{'*' * max(len(name) - 2, 1)}@{host}"


def holds(signup: dict, now: datetime) -> bool:
    """An unfinished sign-up still holding its short name."""
    return signup.get("stage") in ("pending", "verified", "setting_up") and at(signup.get("hold_until", "")) > now
