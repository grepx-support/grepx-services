# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Who may look: the same session token the product's API issues, and the role access-service holds for that user.

`monitor.audience` in the deployment file: admin (default) or staff. Nothing is shown without a valid token.
"""
from __future__ import annotations

from typing import Any, Optional

import grepx_contracts as gc
from grepx_auth import InvalidToken, TokenService
from grepx_common import Roles


class Access:
    def __init__(self, cfg: Any, reader: Any, tokens: Optional[TokenService] = None):
        self.reader, self.tokens = reader, tokens or TokenService.from_env()
        self.roles = Roles.of(cfg)
        self.audience = str((cfg.get("monitor") or {}).get("audience") or "admin").lower()

    def role_of(self, user_id: str, claimed: str) -> str:
        row = self.reader.accepted_one(gc.access.USER_ACCESS, user_id) or {}
        return str(row.get("role") or claimed or self.roles.member)

    def check(self, authorization: str) -> tuple[int, str]:
        """(HTTP status, user id or error code) for an `Authorization: Bearer …` header."""
        if not authorization or not authorization.lower().startswith("bearer "):
            return 401, "LOGIN_REQUIRED"
        try:
            claims = self.tokens.verify(authorization[7:].strip())
        except (InvalidToken, ValueError):
            return 401, "INVALID_SESSION"
        role = self.role_of(str(claims.get("sub") or ""), str(claims.get("role") or ""))
        allowed = self.roles.is_staff(role) if self.audience == "staff" else role == self.roles.admin
        return (200, str(claims.get("sub"))) if allowed else (403, "FORBIDDEN")
