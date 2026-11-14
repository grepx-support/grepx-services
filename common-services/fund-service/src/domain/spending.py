# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Money put to a use against what that use really spent. The caller (the product) supplies the spending of each use
- [{month, category, amount}] in the fund's minor units - so any business can link its own costs (a kitchen: the
outlet's ingredients, labour, rent, other costs). Per use: allocated, spent since the money went in, left, overspent,
the monthly burn (average of the last three months with spending) and spending by category."""
from __future__ import annotations

from .totals import live


def since(entries: list[dict]) -> dict[str, str]:
    """The month each use first got money."""
    out: dict[str, str] = {}
    for e in live(entries):
        if e["kind"] == "allocate":
            p = e.get("purpose") or "Unassigned"
            out[p] = min(out.get(p, "9999"), e["date"][:7])
    return out


def linked(uses: list[dict], entries: list[dict], spending: dict[str, list[dict]]) -> list[dict]:
    start = since(entries)
    out = []
    for u in uses:
        rows = [r for r in spending.get(u["purpose"]) or [] if r.get("month", "") >= start.get(u["purpose"], "")]
        by_month: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        for r in rows:
            by_month[r["month"]] = by_month.get(r["month"], 0) + int(r["amount"])
            by_cat[r.get("category") or "Other"] = by_cat.get(r.get("category") or "Other", 0) + int(r["amount"])
        spent = sum(by_month.values())
        recent = [by_month[m] for m in sorted(by_month)[-3:]]
        out.append({"purpose": u["purpose"], "allocated": u["amount"], "spent": spent, "left": u["amount"] - spent, "over": spent > u["amount"],
                    "pct": round(spent * 100 / u["amount"], 1) if u["amount"] else None, "burn": round(sum(recent) / len(recent)) if recent else 0,
                    "since": start.get(u["purpose"], ""), "months": [{"month": m, "amount": by_month[m]} for m in sorted(by_month)],
                    "categories": sorted(({"category": c, "amount": a} for c, a in by_cat.items()), key=lambda c: -c["amount"])})
    return out
