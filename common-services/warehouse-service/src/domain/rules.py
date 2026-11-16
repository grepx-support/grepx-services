# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bins and pick lines: what a valid bin and a valid line look like."""
from __future__ import annotations

ZONES = ("dry", "chilled", "frozen", "packaging")      # the default zones, when a product names none


def clean_bin(raw: dict, zones: tuple = ZONES) -> dict:
    code = " ".join(str(raw.get("code") or "").split()).upper()
    if not 1 <= len(code) <= 20:
        raise ValueError("INVALID_CODE")
    zone = str(raw.get("zone") or zones[0]).lower()
    if zone not in zones:
        raise ValueError("INVALID_ZONE")
    try:
        capacity = max(0, int(raw.get("capacity") or 0))
    except (TypeError, ValueError):
        raise ValueError("INVALID_QUANTITY")
    level = str(raw.get("level") or "")[:20]
    return {"code": code, "zone": zone, "note": str(raw.get("note") or "")[:120], "active": raw.get("active") is not False,
            **({"capacity": capacity} if capacity else {}), **({"level": level} if level else {})}


def clean_lines(lines) -> list[dict]:
    out = {}
    for line in lines or []:
        try:
            qty = float(line.get("qty"))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("INVALID_QUANTITY")
        if qty <= 0:
            raise ValueError("INVALID_QUANTITY")
        key = str(line.get("item_id") or "")
        out[key] = round(out.get(key, 0) + qty, 4)
    if not out:
        raise ValueError("NO_LINES")
    return [{"item_id": k, "qty": q} for k, q in out.items()]
