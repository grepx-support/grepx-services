# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Which firing slot a schedule is in right now (None = not due). Pure - kept for the callers that only know kind,
every and at; the rules themselves are in rules.py."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .rules import rule_of


def due_slot(kind: str, now: datetime, every_minutes: int = 0, at: str = "", cron: str = "", tz: str = "",
             since: Optional[datetime] = None) -> Optional[str]:
    try:
        return rule_of(kind, every_minutes, at, cron, tz).due(now, since)
    except ValueError:
        return None
