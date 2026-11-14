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

from .totals import totals


def balance_sheet(funds: list[dict], entries: list[dict]) -> dict:
    cash = in_use = owed = capital = paid_back = costs = loan_paid = loan_interest = loan_costs = 0
    for f in funds:
        t = totals([e for e in entries if e["fund_id"] == f["fund_id"]], f.get("kind") == "loan")
        cash += t["available"]
        in_use += t["allocated"]
        if f.get("kind") == "loan":
            owed += t["owed"]
            loan_paid, loan_interest, loan_costs = loan_paid + t["returned"], loan_interest + t["interest"], loan_costs + t["costs"]
        else:
            capital, paid_back, costs = capital + t["received"], paid_back + t["returned"], costs + t["costs"]
    equity = capital - paid_back - costs + loan_paid - loan_interest - loan_costs
    return {"assets": [["Cash in the funds", cash], ["Put to use (at cost)", in_use]], "assets_total": cash + in_use,
            "liabilities": [["Loans owed", owed]], "liabilities_total": owed,
            "equity": [["Capital put in", capital], ["Paid back to partners", -paid_back], ["Fund costs", -costs], ["Loan repayments made by the business", loan_paid],
                       ["Loan interest", -loan_interest], ["Loan costs", -loan_costs]], "equity_total": equity,
            "balances": cash + in_use == owed + equity}


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
