# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Which firing slot a schedule is in right now (None = not due yet today). Pure."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def due_slot(kind: str, now: datetime, every_minutes: int = 0, at: str = "") -> Optional[str]:
    if kind == "EVERY_MINUTES" and every_minutes > 0:
        minutes = (now.hour * 60 + now.minute) // every_minutes * every_minutes
        return f"{now:%Y%m%d}T{minutes // 60:02d}{minutes % 60:02d}"
    if kind == "DAILY_AT" and at:
        hour, minute = (int(x) for x in at.split(":"))
        return f"{now:%Y%m%d}" if (now.hour, now.minute) >= (hour, minute) else None
    return None
