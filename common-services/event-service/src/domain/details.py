# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Event detail validation and cloning dates. Pure."""
from __future__ import annotations

from datetime import date, timedelta


class DetailsError(ValueError):
    pass


def clean_details(raw: dict, partial: bool = False) -> dict:
    out = {}
    for key in ("title", "venue"):
        if key in raw or not partial:
            value = str(raw.get(key) or "").strip()
            if not value:
                raise DetailsError("MISSING_FIELD")
            out[key] = value[:200]
    if "event_date" in raw or not partial:
        try:
            out["event_date"] = date.fromisoformat(str(raw.get("event_date"))).isoformat()
        except ValueError as exc:
            raise DetailsError("INVALID_DATE") from exc
    for key in ("time_slot", "description"):
        if key in raw:
            out[key] = str(raw.get(key) or "").strip()
    if raw.get("capacity") not in (None, ""):
        try:
            capacity = int(raw["capacity"])
        except (TypeError, ValueError) as exc:
            raise DetailsError("INVALID_CAPACITY") from exc
        if not 1 <= capacity <= 5000:
            raise DetailsError("INVALID_CAPACITY")
        out["capacity"] = capacity
    return out


def suggested_clone_date(source: str, today: date) -> str:
    """A week after the source event, but never in the past."""
    return max(date.fromisoformat(source) + timedelta(days=7), today).isoformat()
