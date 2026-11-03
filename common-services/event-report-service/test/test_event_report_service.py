# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""event-report-service: event numbers (+ the blood product plugin's figures, as configured) and retrospective."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "event_report_requests", handle, cfg.live_criteria)
    harness.seed("events", "d1", {"title": "Town Hall", "capacity": 10})
    harness.seed("slots", "s1", {"event_id": "d1", "starts_at": "10:00", "ends_at": "10:30", "capacity": 4})
    harness.seed("people", "ann", {"blood_group": "O-"})
    rows = [("ann", "attended", "online", "s1"), ("bob", "no_show", "online", "s1"), ("cat", "attended", "walkin", ""), ("dan", "interested", "online", "")]
    for donor, state, source, slot in rows:
        harness.seed("bookings", f"d1-{donor}", {"event_id": "d1", "person_id": donor, "state": state, "source": source, "slot_id": slot})
    harness.seed("donations", "x", {"donor_id": "ann", "drive_id": "d1", "donated_on": "2026-01-01"})   # product table, product names
    return harness


def call(h, **f):
    return h.call("event_report_requests", "event-report-service", {"event_id": "d1", **f})


def test_snapshot_numbers(h):
    assert call(h, action="SNAPSHOT").ok
    s = h.read.accepted_one("event_reports", "d1")["stats"]
    assert (s["registered"], s["attended"], s["no_show"], s["walk_ins"], s["show_rate"], s["fill_rate"]) == (4, 2, 1, 1, 67, 75)
    assert s["blood_groups"] == {"O-": 1, "Unknown": 1} and s["first_timers"] == 1 and s["slots"][0]["booked"] == 1
    assert (s["units"], s["event"]["title"], s["slots"][0]["time"]) == (1, "Town Hall", "10:00")


def test_retro_should_keep_stats_and_validate_rating(h):
    call(h, action="SNAPSHOT")
    assert call(h, action="SAVE_RETRO", rating=9).reason == "INVALID_RATING"
    assert call(h, action="SAVE_RETRO", went_well="Fast queue", actions="More chairs\nEarlier start", rating=4).ok
    report = h.read.accepted_one("event_reports", "d1")
    assert report["rating"] == 4 and report["stats"]["attended"] == 2 and report["actions"].splitlines()[1] == "Earlier start"
