# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""slot-service: planning, regeneration guard, capacity limits."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from domain import PlanError, plan_slots
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
PLAN = {"start": "10:00", "end": "11:00", "minutes": 30, "capacity": 2}


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "slot_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("slot_requests", "slot-service", f)


def slots(h):
    return sorted(h.read.accepted("slots", event_id="d1"), key=lambda s: s["starts_at"])


def test_plan_should_cut_consecutive_slots():
    assert [s["starts_at"] for s in plan_slots("10:00", "11:15", 30, 8)] == ["10:00", "10:30", "11:00"]
    assert plan_slots("10:00", "11:15", 30, 8)[-1]["ends_at"] == "11:15"
    with pytest.raises(PlanError):
        plan_slots("12:00", "11:00", 30, 8)


def test_generate_should_create_slots_and_report_capacity(h):
    v = call(h, action="GENERATE", event_id="d1", plan=PLAN)
    assert v.fields["capacity"] == 4 and len(slots(h)) == 2


def test_regenerate_should_refuse_when_booked(h):
    call(h, action="GENERATE", event_id="d1", plan=PLAN)
    h.seed("bookings", "r1", {"slot_id": slots(h)[0]["_key"], "state": "confirmed"})
    assert call(h, action="GENERATE", event_id="d1", plan=PLAN).reason == "HAS_BOOKINGS"


def test_capacity_should_not_drop_below_booked(h):
    call(h, action="GENERATE", event_id="d1", plan=PLAN)
    sid = slots(h)[0]["_key"]
    h.seed("bookings", "r1", {"slot_id": sid, "state": "confirmed"})
    h.seed("bookings", "r2", {"slot_id": sid, "state": "no_show"})
    assert call(h, action="SET_CAPACITY", slot_id=sid, value=0).reason == "BELOW_BOOKED"
    assert call(h, action="SET_CAPACITY", slot_id=sid, delta=1).fields["capacity"] == 3
    assert call(h, action="SET_CAPACITY", slot_id=sid, value=501).reason == "TOO_HIGH"


def test_set_all_should_respect_bookings(h):
    call(h, action="GENERATE", event_id="d1", plan=PLAN)
    h.seed("bookings", "r1", {"slot_id": slots(h)[0]["_key"], "state": "confirmed"})
    h.seed("bookings", "r2", {"slot_id": slots(h)[0]["_key"], "state": "confirmed"})
    assert call(h, action="SET_ALL", event_id="d1", value=1).fields["capacity"] == 3
