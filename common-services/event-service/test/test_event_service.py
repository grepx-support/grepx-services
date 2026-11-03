# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""event-service with slot-service: create with slots, clone, images, complete/reopen rules."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness, load_service
from grepx_config import load_config

from routes import handle

HERE = Path(__file__).resolve().parents[1]
cfg = load_config(HERE / "config")
TODAY = date.today().isoformat()


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "event_requests", handle, cfg.live_criteria)
    slot_handle, slot_cfg, _ = load_service(HERE.parent / "slot-service")
    return harness.add(slot_cfg, "slot_requests", slot_handle, slot_cfg.live_criteria)


def call(h, **f):
    return h.call("event_requests", "event-service", f)


def create(h, **f):
    return call(h, **{"action": "CREATE", "title": "Town Hall Event", "venue": "Town Hall", "event_date": TODAY, **f})


def test_create_with_plan_should_generate_slots(h):
    did = create(h, slot_plan={"start": "10:00", "end": "12:00", "minutes": 30, "capacity": 8}).fields["event_id"]
    assert len(h.rows("slots", event_id=did, status="ACCEPTED")) == 4
    assert h.read.accepted_one("events", did)["state"] == "open"


def test_create_without_title_should_reject(h):
    assert call(h, action="CREATE", venue="x", event_date=TODAY).reason == "MISSING_FIELD"


def test_clone_should_copy_slots_to_new_date(h):
    did = create(h, slot_plan={"start": "10:00", "end": "11:00", "minutes": 30, "capacity": 5}).fields["event_id"]
    h.settle()
    clone = call(h, action="CLONE", source_event_id=did).fields["event_id"]
    copy = h.read.accepted_one("events", clone)
    assert copy["event_date"] == (date.today() + timedelta(days=7)).isoformat()
    assert [s["capacity"] for s in h.rows("slots", event_id=clone, status="ACCEPTED")] == [5, 5]


def test_images_should_limit_to_three_and_set_cover(h):
    did = create(h).fields["event_id"]
    assert call(h, action="SET_IMAGES", event_id=did, images=["a", "b", "c", "d"]).reason == "TOO_MANY_IMAGES"
    call(h, action="SET_IMAGES", event_id=did, images=["m2", "m1"])
    assert h.read.accepted_one("events", did)["image_url"] == "m2"


def test_complete_should_wait_for_event_day(h):
    future = create(h, event_date=(date.today() + timedelta(days=3)).isoformat()).fields["event_id"]
    assert call(h, action="COMPLETE", event_id=future).reason == "TOO_EARLY"
    did = create(h).fields["event_id"]
    assert call(h, action="COMPLETE", event_id=did, voucher={"title": "Free coffee"}).ok
    assert call(h, action="COMPLETE", event_id=did).reason == "ALREADY_COMPLETED"
    assert call(h, action="REOPEN", event_id=did).ok and h.read.accepted_one("events", did)["state"] == "open"


def test_clone_should_take_a_new_title_and_may_skip_slots(h):
    did = call(h, action="CREATE", title="Town Hall", venue="Hall", event_date="2030-01-05",
               slot_plan={"start": "10:00", "end": "11:00", "minutes": 30, "capacity": 2}).fields["event_id"]
    h.settle()
    clone = call(h, action="CLONE", source_event_id=did, title="Town Hall II", copy_slots=False).fields["event_id"]
    assert h.read.accepted_one("events", clone)["title"] == "Town Hall II"
    assert h.read.accepted("slots", event_id=clone) == []
