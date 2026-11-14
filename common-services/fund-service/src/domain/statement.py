# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""An investor's (or lender's) statement: per fund what they promised, put in, got back, their share and what is still
promised, with every movement of theirs in the period (and the money as it was paid when it came in another currency)."""
from __future__ import annotations

from .totals import live, parties

THEIRS = ("commit", "receive", "return", "interest")


def statement(party_id: str, funds: list[dict], entries: list[dict], names: dict[str, str], first: str, last: str) -> dict:
    out = []
    for f in funds:
        mine = [e for e in live(entries) if e["fund_id"] == f["fund_id"] and e["date"] <= last]
        me = next((p for p in parties(mine, names) if p["party_id"] == party_id), None)
        if me is None:
            continue
        lines = [{"date": e["date"], "kind": e["kind"], "amount": e["amount"], "ref": e.get("ref", ""), "note": e.get("note", ""),
                  "original": e.get("original")} for e in mine if e.get("party_id") == party_id and e["kind"] in THEIRS and e["date"] >= first]
        out.append({"fund_id": f["fund_id"], "name": f["name"], "kind": f.get("kind", ""), "currency": f["currency"], **{k: me[k] for k in
                    ("committed", "received", "returned", "interest", "pending", "share_pct")}, "net": me["received"] - me["returned"], "lines": lines})
    return {"party_id": party_id, "name": names.get(party_id, ""), "first": first, "last": last, "funds": out}
