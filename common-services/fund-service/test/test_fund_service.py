# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""fund-service: promises, money in, uses, paybacks, shares, overdue, loans, currency kept per fund, reversing."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import minor, overdue, parties, totals
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


def test_rules():
    assert minor("1234.565", "INR") == 123457 and minor(500, "JPY") == 500
    for bad in ("x", 0, -5):
        with pytest.raises(ValueError):
            minor(bad, "INR")
    e = [{"kind": "commit", "amount": 1000, "party_id": "a", "date": "2026-01-01", "due": "2026-02-01"},
         {"kind": "commit", "amount": 500, "party_id": "b", "date": "2026-01-01", "due": "2026-03-01"},
         {"kind": "receive", "amount": 600, "party_id": "a", "date": "2026-01-10"}, {"kind": "receive", "amount": 500, "party_id": "b", "date": "2026-01-10"},
         {"kind": "allocate", "amount": 700, "purpose": "New outlet", "date": "2026-01-20"}, {"kind": "release", "amount": 100, "purpose": "New outlet", "date": "2026-01-25"},
         {"kind": "return", "amount": 50, "party_id": "a", "date": "2026-02-10"}, {"kind": "cost", "amount": 10, "date": "2026-02-10"},
         {"kind": "receive", "amount": 999, "party_id": "a", "date": "2026-02-11", "reversed": True}]
    t = totals(e)
    assert (t["committed"], t["received"], t["pending"], t["allocated"], t["available"]) == (1500, 1100, 400, 600, 440)
    shares = {p["party_id"]: p for p in parties(e, {"a": "Asha", "b": "Bala"})}
    assert shares["a"]["pending"] == 400 and round(shares["a"]["share_pct"] + shares["b"]["share_pct"]) == 100
    assert overdue(e, "2026-02-15") == [{"party_id": "a", "due": "2026-02-01", "missing": 400, "fund_id": ""}]


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "fund_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("fund_requests", "fund-service", {"tenant_id": "b1", "actor_name": "Owner", **f})


def test_a_fund_from_promise_to_payback(h):
    seed = call(h, action="SAVE_FUND", name="Seed round", kind="equity", currency="inr", target=5000000).fields["fund"]
    assert seed["currency"] == "INR" and seed["target"] == 500000000
    assert call(h, action="SAVE_FUND", fund_id=seed["fund_id"], name="Seed round 1").fields["fund"]["target"] == 500000000
    loan = call(h, action="SAVE_FUND", name="Bank loan", kind="loan", currency="INR", rate_pct=11.5).fields["fund"]
    asha = call(h, action="SAVE_PARTY", name="Asha Capital").fields["party"]["party_id"]
    bank = call(h, action="SAVE_PARTY", name="HDFC Bank", kind="lender").fields["party"]["party_id"]
    rec = lambda **f: call(h, action="RECORD", fund_id=seed["fund_id"], **f)  # noqa: E731
    assert rec(kind="commit", party_id=asha, amount=3000000, date="2026-01-05", due="2026-02-01").ok
    assert rec(kind="receive", party_id="ghost", amount=10).reason == "UNKNOWN_PARTY"
    assert rec(kind="receive", party_id=asha, amount=2000000, date="2026-01-20").ok
    assert rec(kind="receive", party_id=asha, amount=10, currency="USD").reason == "CURRENCY_MISMATCH"
    assert rec(kind="allocate", amount=2500000, purpose="Lower Parel outlet").reason == "NOT_ENOUGH_AVAILABLE"
    assert rec(kind="allocate", amount=1500000, purpose="Lower Parel outlet", date="2026-01-25").ok
    wrong = rec(kind="cost", amount=99999, note="typo").fields["entry"]["entry_id"]
    assert call(h, action="REVERSE", entry_id=wrong, reason="typo").ok and call(h, action="REVERSE", entry_id=wrong).reason == "ALREADY_REVERSED"
    call(h, action="RECORD", fund_id=loan["fund_id"], kind="receive", party_id=bank, amount=1000000, date="2026-01-10")
    call(h, action="RECORD", fund_id=loan["fund_id"], kind="interest", party_id=bank, amount=9583, date="2026-02-10")
    call(h, action="RECORD", fund_id=loan["fund_id"], kind="return", party_id=bank, amount=50000, date="2026-02-10")
    o = call(h, action="OVERVIEW", today="2026-02-15").fields
    assert o["totals"]["INR"]["received"] == 300000000 and o["totals"]["INR"]["pending"] == 100000000
    assert o["overdue"][0]["name"] == "Asha Capital" and o["overdue"][0]["missing"] == 100000000
    f = call(h, action="FUND", fund_id=seed["fund_id"], today="2026-02-15").fields
    assert f["totals"]["available"] == 50000000 and f["uses"] == [{"purpose": "Lower Parel outlet", "amount": 150000000}]
    assert f["parties"][0]["share_pct"] == 100.0 and len(f["entries"]) == 4 and f["months"][0]["in"] == 200000000
    loan_now = call(h, action="FUND", fund_id=loan["fund_id"]).fields["totals"]
    assert loan_now["owed"] == 100000000 + 958300 - 5000000
    assert h.call("fund_requests", "fund-service", {"tenant_id": "b2", "action": "FUND", "fund_id": seed["fund_id"]}).reason == "UNKNOWN_FUND"
