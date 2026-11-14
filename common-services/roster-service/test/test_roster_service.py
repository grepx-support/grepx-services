# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""roster-service: shifts at several sites, clashes across sites, copy / publish a week, cost, PIN clocking."""
from datetime import datetime
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clashes, hour_cost, late_minutes, paid_minutes, shift_for, week_summary
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "roster_requests", handle, cfg.live_criteria)
    harness.seed("employees", "e1", {"tenant_id": "b1", "name": "Meera", "sites": ["k1", "s1"], "pay": {"basis": "hourly", "rate": 200}})
    harness.seed("employees", "e2", {"tenant_id": "b1", "name": "Ravi", "sites": ["s1"], "pay": {"basis": "monthly", "rate": 34666.67, "weekly_hours": 40}})
    harness.seed("leaves", "l1", {"tenant_id": "b1", "employee_id": "e2", "state": "approved", "first": "2026-11-18", "last": "2026-11-19", "type_name": "Sick leave"})
    harness.seed("employees", "x9", {"tenant_id": "b2", "name": "Other", "sites": ["z"]})
    return harness


def call(h, **f):
    return h.call("roster_requests", "roster-service", {"tenant_id": "b1", **f})


def test_rules():
    night = {"date": "2026-11-16", "start": "22:00", "end": "06:00", "break_min": 30, "employee_id": "e1"}
    assert paid_minutes(night) == 450
    assert clashes({**night, "shift_id": "n"}, [{"date": "2026-11-17", "start": "05:00", "end": "09:00", "employee_id": "e1", "shift_id": "m"}])
    assert not clashes({**night, "shift_id": "n"}, [{"date": "2026-11-17", "start": "06:00", "end": "09:00", "employee_id": "e1", "shift_id": "m"}])
    assert round(hour_cost({"pay": {"basis": "monthly", "rate": 34666.67, "weekly_hours": 40}}), 2) == 200.0
    s = {"date": "2026-11-16", "start": "09:00", "end": "17:00"}
    assert shift_for([s], datetime(2026, 11, 16, 8, 0)) == s and shift_for([s], datetime(2026, 11, 16, 19, 0)) is None
    assert late_minutes(s, datetime(2026, 11, 16, 9, 4)) == 0 and late_minutes(s, datetime(2026, 11, 16, 9, 12)) == 12
    week = week_summary([{**s, "employee_id": "e1"}, {**s, "employee_id": ""}], {"e1": {"pay": {"basis": "hourly", "rate": 100}}})
    assert week["minutes"] == 960 and week["people"][0]["cost"] == 800 and week["open_shifts"] == 1


def test_a_week_across_sites(h):
    a = call(h, action="SAVE_SHIFT", site_id="k1", employee_id="e1", date="2026-11-16", start="07:00", end="15:00", break_min=30, role="Cook")
    assert a.ok and a.fields["shift"]["published"] is False
    clash = call(h, action="SAVE_SHIFT", site_id="s1", employee_id="e1", date="2026-11-16", start="14:00", end="20:00")
    assert clash.reason == "DOUBLE_BOOKED"                                   # same person, another outlet, same time
    assert call(h, action="SAVE_SHIFT", site_id="s1", employee_id="e1", date="2026-11-16", start="16:00", end="20:00").ok
    assert call(h, action="SAVE_SHIFT", site_id="s1", employee_id="x9", date="2026-11-16", start="09:00", end="10:00").reason == "UNKNOWN_EMPLOYEE"
    assert call(h, action="SAVE_SHIFT", site_id="s1", date="2026-11-17", start="09:00", end="17:00").ok      # open shift
    assert call(h, action="SAVE_SHIFT", site_id="s1", employee_id="e2", date="2026-11-17", start="25:00", end="17:00").reason == "INVALID_TIME"
    assert call(h, action="SAVE_SHIFT", site_id="s1", employee_id="e2", date="2026-11-19", start="09:00", end="17:00").reason == "ON_LEAVE"
    w = call(h, action="WEEK", week="2026-11-18").fields["week"]
    assert w["leaves"][0]["employee_id"] == "e2"
    assert len(w["shifts"]) == 3 and w["summary"]["open_shifts"] == 1 and w["summary"]["people"][0]["minutes"] == 450 + 240
    assert len(call(h, action="WEEK", week="2026-11-18", site_id="k1").fields["week"]["shifts"]) == 1
    assert call(h, action="PUBLISH_WEEK", week="2026-11-16", site_id="s1").fields["published"] == 2
    copy = call(h, action="COPY_WEEK", site_id="s1", from_week="2026-11-16", to_week="2026-11-23")
    assert copy.fields == {**copy.fields, "copied": 2, "skipped": 0}
    assert call(h, action="COPY_WEEK", site_id="s1", from_week="2026-11-16", to_week="2026-11-23").fields["copied"] == 0
    sid = a.fields["shift"]["shift_id"]
    assert call(h, action="REMOVE_SHIFT", shift_id=sid).ok
    assert h.call("roster_requests", "roster-service", {"tenant_id": "b2", "action": "REMOVE_SHIFT", "shift_id": sid}).reason == "UNKNOWN_SHIFT"


def test_clock_in_and_out_with_a_pin(h):
    call(h, action="SAVE_SHIFT", site_id="k1", employee_id="e1", date="2026-11-16", start="09:00", end="17:00", break_min=30)
    assert call(h, action="SET_PIN", employee_id="e1", pin="12a4").reason == "INVALID_PIN"
    assert call(h, action="SET_PIN", employee_id="e1", pin="4321").ok
    assert call(h, action="CLOCK", employee_id="e1", site_id="k1", pin="0000", at="2026-11-16T09:20").reason == "WRONG_PIN"
    assert call(h, action="CLOCK", employee_id="e1", site_id="zz", pin="4321", at="2026-11-16T09:20").reason == "NOT_AT_THIS_SITE"
    came = call(h, action="CLOCK", employee_id="e1", site_id="k1", pin="4321", at="2026-11-16T09:20")
    assert came.fields["clocked"] == "in" and came.fields["attendance"]["late_min"] == 20 and came.fields["attendance"]["shift_id"]
    went = call(h, action="CLOCK", employee_id="e1", site_id="k1", verified=True, at="2026-11-16T17:05")
    assert went.fields["clocked"] == "out" and went.fields["attendance"]["worked_min"] == 465 - 30
    assert call(h, action="WEEK", week="2026-11-16").fields["week"]["attendance"][0]["worked_min"] == 435
