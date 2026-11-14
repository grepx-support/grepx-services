# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The movements of a fund. Each kind moves one of the fund's running totals (Strategy: one small rule per kind):

  commit    a party promises an amount (due by a date)          -> committed
  receive   money comes in from a party                          -> received (pending = committed - received)
  allocate  money is put to a use (a project, a place, a purpose) -> allocated
  release   money put to a use comes back unused                 -> allocated goes down
  return    money goes back to a party (dividend, repayment)     -> returned
  interest  interest charged on a loan, owed to the lender       -> interest
  cost      a cost of the fund itself (fees, bank charges)       -> costs

available = received - allocated - returned - costs (a loan: repayments not counted); a loan's balance = received + interest - returned."""
from __future__ import annotations

from datetime import date

KINDS = ("commit", "receive", "allocate", "release", "return", "interest", "cost")
NEEDS_PARTY = ("commit", "receive", "return", "interest")
TAKES_CASH = ("allocate", "return", "cost")         # a loan's repayments are paid by the business, not from the fund
FUND_KINDS = ("equity", "loan", "grant", "owner")


def clean_entry(raw: dict) -> dict:
    kind = str(raw.get("kind") or "")
    if kind not in KINDS:
        raise ValueError("INVALID_KIND")
    try:
        on = date.fromisoformat(str(raw.get("date") or date.today().isoformat())[:10]).isoformat()
        due = date.fromisoformat(str(raw["due"])[:10]).isoformat() if raw.get("due") else ""
    except ValueError:
        raise ValueError("INVALID_DATE")
    return {"kind": kind, "date": on, "due": due if kind == "commit" else "", "party_id": str(raw.get("party_id") or ""),
            "purpose": " ".join(str(raw.get("purpose") or "").split())[:80], "ref": " ".join(str(raw.get("ref") or "").split())[:60],
            "note": str(raw.get("note") or "").strip()[:300]}


def clean_fund(raw: dict) -> dict:
    name = " ".join(str(raw.get("name") or "").split())[:80]
    if not name:
        raise ValueError("INVALID_NAME")
    kind = str(raw.get("kind") or "equity")
    if kind not in FUND_KINDS:
        raise ValueError("INVALID_KIND")
    try:
        rate = float(raw.get("rate_pct") or 0)
    except (TypeError, ValueError):
        raise ValueError("INVALID_AMOUNT")
    return {"name": name, "kind": kind, "rate_pct": rate, "purpose": " ".join(str(raw.get("purpose") or "").split())[:200],
            "opened": str(raw.get("opened") or date.today().isoformat())[:10], "closed": bool(raw.get("closed"))}
