# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""leave-service: days without weekly days off, balances with pro-rating and carry-over, overlaps, approve, cancel."""
from datetime import date
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import DEFAULTS, allowance, balance, leave_days
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "leave_requests", handle, cfg.live_criteria)
    harness.seed("employees", "e1", {"tenant_id": "b1", "name": "Meera", "sites": ["k1"], "start_date": "2024-01-01", "active": True})
    harness.seed("employees", "e2", {"tenant_id": "b1", "name": "Ravi", "sites": ["s1"], "start_date": "2026-07-01", "active": True})
    return harness


def call(h, **f):
    return h.call("leave_requests", "leave-service", {"tenant_id": "b1", **f})


def test_rules():
    assert leave_days(date(2026, 11, 14), date(2026, 11, 17)) == 3.0              # Sat..Tue, Sunday off
    assert leave_days(date(2026, 11, 14), date(2026, 11, 17), days_off=(5, 6)) == 2.0
    assert leave_days(date(2026, 11, 16), date(2026, 11, 16), half=True) == 0.5
    annual = DEFAULTS[0]
    assert allowance(annual, 2026, "2026-07-01") == 9.0 and allowance(annual, 2026, "2027-01-01") == 0.0
    b = balance(annual, [{"type_id": "annual", "state": "approved", "first": "2025-03-01", "days": 10}], 2026, "2024-01-01")
    assert (b["carried"], b["allowance"], b["left"]) == (6.0, 24.0, 24.0)       # 18 - 10 = 8 left last year, carry up to 6


def test_request_approve_balance_calendar(h):
    a = call(h, action="REQUEST", employee_id="e1", type_id="annual", first="2026-12-01", last="2026-12-05", note="Wedding")
    assert a.ok and a.fields["leave"]["days"] == 5 and a.fields["leave"]["state"] == "pending"
    assert call(h, action="REQUEST", employee_id="e1", type_id="sick", first="2026-12-04").reason == "OVERLAPS"
    assert call(h, action="REQUEST", employee_id="e2", type_id="annual", first="2026-12-01", last="2026-12-12").reason == "NOT_ENOUGH_BALANCE"
    assert call(h, action="REQUEST", employee_id="e2", type_id="unpaid", first="2026-12-01", last="2026-12-12").ok   # unlimited
    lid = a.fields["leave"]["leave_id"]
    assert call(h, action="DECIDE", leave_id=lid, approve=True, actor_name="Owner").fields["leave"]["state"] == "approved"
    assert call(h, action="DECIDE", leave_id=lid, approve=False).reason == "ALREADY_DECIDED"
    bal = call(h, action="BALANCES", year=2026, employee_id="e1").fields["people"][0]["types"]
    annual = next(t for t in bal if t["type_id"] == "annual")
    assert annual["taken"] == 5 and annual["left"] == annual["allowance"] - 5
    cal = call(h, action="CALENDAR", first="2026-12-01", last="2026-12-31", site_id="k1").fields["leaves"]
    assert [l["name"] for l in cal] == ["Meera"]
    assert call(h, action="CANCEL", leave_id=lid, today="2026-12-02").reason == "ALREADY_STARTED"
    assert call(h, action="CANCEL", leave_id=lid, today="2026-11-20").ok
    assert call(h, action="SAVE_TYPE", name="Comp off", days_per_year=0, unlimited=True).fields["type"]["type_id"] == "comp_off"
    assert call(h, action="SAVE_TYPE", type_id="casual", name="Casual leave", days_per_year=0, active=False).ok
    kinds = [t["type_id"] for t in call(h, action="BALANCES", year=2026).fields["types"]]
    assert "comp_off" in kinds and "casual" not in kinds
    assert call(h, action="REQUEST", employee_id="e1", type_id="casual", first="2026-12-20").reason == "UNKNOWN_TYPE"
