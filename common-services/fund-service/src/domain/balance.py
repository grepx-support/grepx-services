# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The capital position of the business across its funds, as a balance sheet that always balances:

  Assets       cash still in the funds + money put to use (at cost, less what was written off as spent)
  Liabilities  what is owed on loans (received + interest - repaid)
  Equity       capital put in by owners / partners / investors - paid back to them - fund costs;
               + loan repayments the business made - loan interest - loan costs
And utilisation: of the money put to use, how much was actually spent."""
from __future__ import annotations

from .totals import live, totals, uses


def line(label: str, rows: list[tuple[str, int]]) -> dict:
    """A balance-sheet line with the rows behind it (drill-down)."""
    rows = [(n, a) for n, a in rows if a]
    return {"label": label, "amount": sum(a for _, a in rows), "rows": [{"label": n, "amount": a} for n, a in sorted(rows, key=lambda r: -abs(r[1]))]}


def balance_sheet(funds: list[dict], entries: list[dict], names: dict[str, str] | None = None, as_of: str = "") -> dict:
    """As of a date (default: everything). Each line carries its rows: per fund, per use, per lender, per partner."""
    names = names or {}
    entries = [e for e in entries if not as_of or e["date"] <= as_of]
    cash, in_use, owed, capital, paid_back, costs, loan_side = [], {}, [], {}, {}, [], []
    for f in funds:
        mine = [e for e in entries if e["fund_id"] == f["fund_id"]]
        loan, t = f.get("kind") == "loan", totals(mine, f.get("kind") == "loan")
        cash.append((f["name"], t["available"]))
        for u in uses(mine):
            in_use[u["purpose"]] = in_use.get(u["purpose"], 0) + u["amount"]
        if loan:
            owed.append((f["name"], t["owed"]))
            loan_side += [(f"{f['name']}: repaid by the business", t["returned"]), (f"{f['name']}: interest", -t["interest"]), (f"{f['name']}: costs", -t["costs"])]
            continue
        costs.append((f["name"], -t["costs"]))
        for e in live(mine):
            if e["kind"] in ("receive", "return") and e.get("party_id"):
                book = capital if e["kind"] == "receive" else paid_back
                who = names.get(e["party_id"], "?")
                book[who] = book.get(who, 0) + int(e["amount"]) * (1 if e["kind"] == "receive" else -1)
    assets = [line("Cash in the funds", cash), line("Put to use (at cost)", list(in_use.items()))]
    liabilities = [line("Loans owed", owed)]
    equity = [line("Capital put in", list(capital.items())), line("Paid back to partners", list(paid_back.items())), line("Fund costs", costs),
              line("Loans: repaid by the business less interest and costs", loan_side)]
    a, l, q = (sum(x["amount"] for x in side) for side in (assets, liabilities, equity))
    return {"as_of": as_of, "assets": assets, "assets_total": a, "liabilities": liabilities, "liabilities_total": l, "equity": equity,
            "equity_total": q, "balances": a == l + q}


def utilisation(entries: list[dict]) -> list[dict]:
    """Per use: put to use (net of money come back) against actually spent."""
    by: dict[str, dict] = {}
    for e in entries:
        if e.get("reversed") or e["kind"] not in ("allocate", "release", "spend"):
            continue
        u = by.setdefault(e.get("purpose") or "Unassigned", {"purpose": e.get("purpose") or "Unassigned", "allocated": 0, "spent": 0})
        u["allocated" if e["kind"] != "spend" else "spent"] += int(e["amount"]) * (-1 if e["kind"] == "release" else 1)
    for u in by.values():
        u["pct"] = round(u["spent"] / u["allocated"] * 100, 1) if u["allocated"] else None
    return sorted(by.values(), key=lambda u: -u["allocated"])
