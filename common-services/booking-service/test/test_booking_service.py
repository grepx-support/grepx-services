# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""booking-service: interest, booking with slots, cancel, move, check-in, marking rules, completion, reminders."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_service.plugins import template_for
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from grepx_config import load_config
from nexus_testkit import MemoryClient

from domain import merge_state
from jobs import handle_event, handle_tick
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
TODAY = date.today().isoformat()


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "booking_requests", handle, cfg.live_criteria)
    harness.seed("events", "d1", {"title": "Town Hall", "event_date": TODAY, "state": "open", "venue": "Hall"})
    harness.seed("slots", "s1", {"event_id": "d1", "starts_at": "10:00", "ends_at": "10:30", "capacity": 1})
    harness.seed("slots", "s2", {"event_id": "d1", "starts_at": "10:30", "ends_at": "11:00", "capacity": 1})
    harness.seed("people", "ann", {"name": "Ann Tan", "email": "ann@x.sg", "phone": "+6591234567"})
    harness.seed("people", "bob", {"name": "Bob Lim", "email": "bob@x.sg", "phone": "+6598765432"})
    return harness


def call(h, **f):
    return h.call("booking_requests", "booking-service", {"event_id": "d1", **f})


def reg(h, key="d1-ann"):
    return h.read.accepted_one("bookings", key)


def test_state_never_downgrades():
    assert merge_state("attended", "interested") == "attended" and merge_state("interested", "confirmed") == "confirmed"
    assert merge_state("cancelled", "interested") == "interested"


def test_booking_should_require_and_fill_slots(h):
    assert call(h, action="BOOK", person_id="ann").reason == "SLOT_REQUIRED"
    assert call(h, action="BOOK", person_id="ann", slot_id="s1").ok
    assert reg(h)["slot_start"] == "10:00" and reg(h)["email"] == "ann@x.sg"
    assert call(h, action="BOOK", person_id="bob", slot_id="s1").reason == "SLOT_FULL"
    assert call(h, action="BOOK", person_id="ann", slot_id="s1").ok  # rebooking own slot is fine


def test_cancel_should_free_slot(h):
    call(h, action="BOOK", person_id="ann", slot_id="s1")
    assert call(h, action="CANCEL", person_id="ann").ok
    assert call(h, action="BOOK", person_id="bob", slot_id="s1").ok


def test_guest_interest_needs_contact_and_upgrades_on_booking(h):
    assert call(h, action="INTEREST", name="Guest").reason == "MISSING_FIELD"
    assert call(h, action="INTEREST", person_id="ann").ok and reg(h)["state"] == "interested"
    call(h, action="BOOK", person_id="ann", slot_id="s2")
    call(h, action="INTEREST", person_id="ann")
    assert reg(h)["state"] == "confirmed"


def test_move_should_notify_and_admin_may_overbook(h):
    call(h, action="BOOK", person_id="ann", slot_id="s1")
    call(h, action="BOOK", person_id="bob", slot_id="s2")
    assert call(h, action="MOVE", booking_id="d1-bob", slot_id="s1").reason == "SLOT_FULL"
    assert call(h, action="MOVE", booking_id="d1-bob", slot_id="s1", override_capacity=True).ok
    assert any(n["template"] == "slot_changed" for n in h.rows("notifications"))


def test_mark_rules(h):
    call(h, action="CHECK_IN", person_id="ann", source="kiosk")
    assert reg(h)["state"] == "confirmed" and reg(h)["source"] == "kiosk"
    assert call(h, action="MARK", booking_id="d1-ann", state="flying").reason == "INVALID_STATE"
    assert call(h, action="MARK", booking_id="d1-ann", state="attended").ok
    h.seed("events", "d2", {"event_date": (date.today() + timedelta(days=2)).isoformat(), "state": "open"})
    call(h, action="INTEREST", event_id="d2", person_id="bob")
    assert call(h, action="MARK", booking_id="d2-bob", state="no_show").reason == "NOT_EVENT_DAY"


def test_completion_should_close_open_bookings(h):
    call(h, action="BOOK", person_id="ann", slot_id="s1")
    call(h, action="BOOK", person_id="bob", slot_id="s2")
    call(h, action="MARK", booking_id="d1-ann", state="attended")
    app = NexusApplication(MemoryClient(h.engine), "events")
    assert handle_event(app, Row("d1", {"status": "ACCEPTED", "state": "completed"}), cfg) == 1
    assert reg(h, "d1-bob")["state"] == "no_show" and reg(h)["state"] == "attended"


def test_reminders_should_go_once_the_day_before(h):
    call(h, action="BOOK", person_id="ann", slot_id="s1")
    app = NexusApplication(MemoryClient(h.engine), "ticks")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert handle_tick(app, Row("t1", {"status": "NEW", "job": "event-reminders"}), cfg, today=yesterday) == 1
    assert handle_tick(app, Row("t2", {"status": "NEW", "job": "event-reminders"}), cfg, today=yesterday) == 0
    assert {n["template"] for n in h.rows("notifications")} == {template_for(cfg, "event_reminder")}   # deployment maps the role


def test_not_eligible_any_day_frees_the_slot_and_sticks(h):
    h.seed("events", "d2", {"event_date": (date.today() + timedelta(days=2)).isoformat(), "state": "open"})
    call(h, action="INTEREST", event_id="d2", person_id="bob")
    assert call(h, action="MARK", booking_id="d2-bob", state="not_eligible").ok      # before the event day too
    call(h, action="INTEREST", event_id="d2", person_id="bob")                               # re-registering does not undo it
    assert reg(h, "d2-bob")["state"] == "not_eligible"
    assert call(h, action="MARK", booking_id="d2-bob", state="confirmed").ok           # staff can change their mind


def test_not_eligible_should_free_the_booked_slot(h):
    call(h, action="BOOK", person_id="ann", slot_id="s1")
    assert call(h, action="BOOK", person_id="bob", slot_id="s1").reason == "SLOT_FULL"
    call(h, action="MARK", booking_id="d1-ann", state="not_eligible")
    assert call(h, action="BOOK", person_id="bob", slot_id="s1").ok
