# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A fund's position from its entries (reversed ones left out): the running totals, each party's committed / paid /
pending / returned and share of what was paid in, the uses money was put to, the months' flow, overdue promises."""
from __future__ import annotations

FIELDS = {"commit": "committed", "receive": "received", "allocate": "allocated", "release": "released", "return": "returned",
          "interest": "interest", "cost": "costs", "spend": "spent"}


def live(entries: list[dict]) -> list[dict]:
    return [e for e in entries if not e.get("reversed")]


def totals(entries: list[dict], loan: bool = False) -> dict:
    t = {f: 0 for f in FIELDS.values()}
    for e in live(entries):
        t[FIELDS[e["kind"]]] += int(e["amount"])
    t["allocated"] -= t.pop("released")
    t["utilised_pct"] = round(t["spent"] / t["allocated"] * 100, 1) if t["allocated"] else None
    t["pending"] = max(0, t["committed"] - t["received"])
    t["available"] = t["received"] - t["allocated"] - t["costs"] - (0 if loan else t["returned"])   # loan repayments come from the business
    t["owed"] = t["received"] + t["interest"] - t["returned"]          # a loan's balance (equity: what the parties put in, net)
    return t


def parties(entries: list[dict], names: dict[str, str]) -> list[dict]:
    rows: dict[str, dict] = {}
    for e in live(entries):
        if not e.get("party_id"):
            continue
        p = rows.setdefault(e["party_id"], {"party_id": e["party_id"], "name": names.get(e["party_id"], "?"), "committed": 0, "received": 0,
                                            "returned": 0, "interest": 0})
        key = FIELDS[e["kind"]]
        if key in p:
            p[key] += int(e["amount"])
    paid = sum(p["received"] for p in rows.values()) or 1
    for p in rows.values():
        p["pending"] = max(0, p["committed"] - p["received"])
        p["share_pct"] = round(p["received"] / paid * 100, 2)
    return sorted(rows.values(), key=lambda p: -p["received"])


def uses(entries: list[dict]) -> list[dict]:
    by: dict[str, int] = {}
    for e in live(entries):
        if e["kind"] in ("allocate", "release"):
            by[e.get("purpose") or "Unassigned"] = by.get(e.get("purpose") or "Unassigned", 0) + (int(e["amount"]) if e["kind"] == "allocate" else -int(e["amount"]))
    return sorted(({"purpose": k, "amount": v} for k, v in by.items() if v), key=lambda u: -u["amount"])


def months(entries: list[dict]) -> list[dict]:
    by: dict[str, dict] = {}
    for e in live(entries):
        m = by.setdefault(e["date"][:7], {"month": e["date"][:7], "in": 0, "out": 0})
        if e["kind"] == "receive":
            m["in"] += int(e["amount"])
        elif e["kind"] in ("allocate", "return", "cost"):
            m["out"] += int(e["amount"])
        elif e["kind"] == "release":
            m["out"] -= int(e["amount"])
    return [by[k] for k in sorted(by)]


def overdue(entries: list[dict], today: str) -> list[dict]:
    """Promises past their due date that are not fully paid yet (by party, oldest first)."""
    out = []
    for p, rows in group_by_party(live(entries)).items():
        paid = sum(int(e["amount"]) for e in rows if e["kind"] == "receive")
        for c in sorted((e for e in rows if e["kind"] == "commit"), key=lambda e: e.get("due") or e["date"]):
            covered = min(paid, int(c["amount"]))
            paid -= covered
            if c.get("due") and c["due"] < today and covered < int(c["amount"]):
                out.append({"party_id": p, "due": c["due"], "missing": int(c["amount"]) - covered, "fund_id": c.get("fund_id", "")})
    return sorted(out, key=lambda o: o["due"])


def group_by_party(entries: list[dict]) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for e in entries:
        if e.get("party_id"):
            by.setdefault(e["party_id"], []).append(e)
    return by
