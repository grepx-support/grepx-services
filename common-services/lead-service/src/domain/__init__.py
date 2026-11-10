# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a usable enquiry looks like (no I/O)."""
from __future__ import annotations

import re

EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")


def _text(value, n: int) -> str:
    return " ".join(str(value or "").split())[:n]


def clean_lead(raw: dict) -> dict:
    """Raises ValueError(reason). A filled hidden 'website' field means a bot filled the form (SPAM)."""
    if raw.get("website"):
        raise ValueError("SPAM")
    name, email = _text(raw.get("name"), 80), _text(raw.get("email"), 200).lower()
    if len(name) < 2:
        raise ValueError("INVALID_NAME")
    if not EMAIL.match(email):
        raise ValueError("INVALID_EMAIL")
    return {"name": name, "email": email, "phone": _text(raw.get("phone"), 30), "company": _text(raw.get("company"), 120),
            "size": _text(raw.get("size"), 40), "message": str(raw.get("message") or "")[:2000], "product": _text(raw.get("product"), 40),
            "kind": _text(raw.get("kind") or "demo", 20)}
