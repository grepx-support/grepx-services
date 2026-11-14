# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""API keys of an organisation: a name, read or write, kept only as a hash of the secret (the BFF makes the key and
shows it once). Pure."""
from __future__ import annotations

import re

SCOPES = ("read", "write")
MAX_ACTIVE = 20


def new_key_row(fields: dict, tenant: str, active_count: int, at: str) -> dict:
    """The api_keys row for a new key. Refuses MISSING_TENANT, INVALID_KEY, INVALID_SCOPE, TOO_MANY_KEYS."""
    if not tenant:
        raise ValueError("MISSING_TENANT")
    key_id, digest = str(fields.get("key_id") or ""), str(fields.get("secret_hash") or "")
    if not re.fullmatch(r"[a-z0-9]{12}", key_id) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("INVALID_KEY")
    scope = str(fields.get("scope") or "read")
    if scope not in SCOPES:
        raise ValueError("INVALID_SCOPE")
    if active_count >= MAX_ACTIVE:
        raise ValueError("TOO_MANY_KEYS")
    name = " ".join(str(fields.get("name") or "API key").split())[:60] or "API key"
    return {"key_id": key_id, "tenant_id": tenant, "name": name, "scope": scope, "secret_hash": digest, "active": True,
            "created_at": at, "created_by": str(fields.get("actor_name") or "")[:80]}
