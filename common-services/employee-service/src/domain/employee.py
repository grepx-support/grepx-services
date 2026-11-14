# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a valid employee record looks like. Sites are the places of the business the person works at (outlets,
kitchens, offices: whatever the product calls them); the home site is one of them. Pay basis is "monthly" (a salary)
or "hourly" (a rate per hour) - payroll-service turns it into pay."""
from __future__ import annotations

import re
from datetime import date

PAY_BASIS = ("monthly", "hourly")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def text(value, most: int) -> str:
    return " ".join(str(value or "").split())[:most]


def day(value, reason: str = "INVALID_DATE") -> str:
    if value in (None, ""):
        return ""
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        raise ValueError(reason)


def pay(raw: dict) -> dict:
    basis = str(raw.get("basis") or "monthly").lower()
    try:
        rate = round(float(raw.get("rate") or 0), 2)
        hours = float(raw.get("weekly_hours") or 0)
    except (TypeError, ValueError):
        raise ValueError("INVALID_PAY")
    if basis not in PAY_BASIS or rate < 0 or not 0 <= hours <= 100:
        raise ValueError("INVALID_PAY")
    return {"basis": basis, "rate": rate, "weekly_hours": hours, "overtime_after": float(raw.get("overtime_after") or 0)}


def clean_employee(raw: dict, current: dict | None = None) -> dict:
    merged = {**(current or {}), **{k: v for k, v in raw.items() if v is not None}}
    name = text(merged.get("name"), 80)
    if len(name) < 2:
        raise ValueError("INVALID_NAME")
    email = str(merged.get("email") or "").strip().lower()
    if email and not EMAIL.match(email):
        raise ValueError("INVALID_EMAIL")
    sites = list(dict.fromkeys(str(s) for s in (merged.get("sites") or []) if s))
    home = str(merged.get("home_site") or (sites[0] if sites else ""))
    if home and home not in sites:
        sites.insert(0, home)
    start, end = day(merged.get("start_date")), day(merged.get("end_date"))
    if start and end and end < start:
        raise ValueError("INVALID_DATE")
    contact = merged.get("emergency") or {}
    return {"name": name, "email": email, "phone": "".join(c for c in str(merged.get("phone") or "") if c.isdigit() or c == "+")[:20],
            "position": text(merged.get("position"), 60), "department": text(merged.get("department"), 60),
            "home_site": home, "sites": sites, "start_date": start, "end_date": end,
            "pay": pay(merged.get("pay") or {}), "user_id": str(merged.get("user_id") or ""),
            "emergency": {"name": text(contact.get("name"), 80), "phone": text(contact.get("phone"), 20)},
            "notes": str(merged.get("notes") or "").strip()[:1000], "documents": merged.get("documents") or [],
            "active": not end or end >= date.today().isoformat()}
