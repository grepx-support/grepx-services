# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""People and companies. Pure."""
from __future__ import annotations

import re

KINDS = ("person", "company")
FIELDS = ("name", "email", "phone", "title", "company_id", "address", "tax_number", "source", "notes", "website", "owner_id", "owner_name", "kind")


def clean_contact(raw: dict, current: dict | None = None) -> dict:
    """The contact row (current values kept where not given). Refuses INVALID_NAME, INVALID_KIND, INVALID_EMAIL."""
    m = {**(current or {}), **{k: raw[k] for k in FIELDS if raw.get(k) is not None}, "tags": raw.get("tags", (current or {}).get("tags", []))}
    name = " ".join(str(m.get("name") or "").split())[:120]
    if not name:
        raise ValueError("INVALID_NAME")
    kind = str(m.get("kind") or "person")
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    email = str(m.get("email") or "").strip().lower()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("INVALID_EMAIL")
    tags = sorted({" ".join(str(t).split()).lower()[:30] for t in m.get("tags") or [] if str(t).strip()})[:20]
    return {**{k: str(m.get(k) or "")[:500] for k in FIELDS}, "name": name, "kind": kind, "email": email, "tags": tags,
            "company_id": "" if kind == "company" else str(m.get("company_id") or "")}
