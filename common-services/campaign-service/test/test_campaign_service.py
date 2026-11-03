# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""campaign-service: audiences, invite filters, broadcasts."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
SOON = (date.today() + timedelta(days=30)).isoformat()


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "campaign_requests", handle, cfg.live_criteria)
    harness.seed("events", "d1", {"title": "Town Hall", "event_date": SOON, "venue": "Hall"})
    harness.seed("people", "ann", {"name": "Ann Tan", "email": "ann@x.sg", "blood_group": "O-", "sex": "Female"})
    harness.seed("people", "bob", {"name": "Bob Lim", "email": "bob@x.sg", "blood_group": "A+", "sex": "Male"})
    harness.seed("people", "vic", {"name": "Vic Ong", "email": "vic@x.sg"})
    harness.seed("user_access", "vic", {"role": "volunteer"})
    harness.seed("donor_stats", "bob", {"count": 1, "last": date.today().isoformat(), "next_eligible": SOON})
    return harness


def call(h, **f):
    return h.call("campaign_requests", "campaign-service", {"channels": ["email"], **f})


def test_eligible_audience_should_skip_waiting_and_staff(h):
    assert call(h, action="ANNOUNCE", event_id="d1", audience="eligible").fields["count"] == 1
    assert {n["recipient"] for n in h.rows("notifications")} == {"ann@x.sg"}


def test_group_and_volunteer_audiences(h):
    assert call(h, action="BROADCAST", audience="group:A+", text="Urgent").fields["count"] == 1
    assert call(h, action="BROADCAST", audience="volunteer", text="Briefing").fields["count"] == 1
    assert call(h, action="BROADCAST", audience="group:Z", text="x").reason == "UNKNOWN_AUDIENCE"


def test_invite_should_exclude_registered_and_filter(h):
    h.seed("bookings", "d1-ann", {"event_id": "d1", "person_id": "ann", "state": "confirmed"})
    v = call(h, action="INVITE", event_id="d1", filters={"sex": "Male"}, preview=True)
    assert v.fields["names"] == ["Bob Lim"]
    assert call(h, action="INVITE", event_id="d1", filters={"eligible_only": True}).fields["count"] == 1


def test_broadcast_needs_text(h):
    assert call(h, action="BROADCAST", audience="donor").reason == "MISSING_TEXT"


def test_publish_social_should_record_each_attempt(h):
    v = h.call("campaign_requests", "campaign-service", {"action": "PUBLISH_SOCIAL", "event_id": "d1", "networks": ["facebook", "telegram"],
                                                          "caption": "Join us!", "link": "https://example.org/event/d1"})
    assert v.ok and set(v.fields["results"]) == {"facebook", "telegram"}
    posts = h.rows("social_posts")
    assert len(posts) == 2 and all(p["post_status"] == "failed" and "not set up" in p["error"] for p in posts)


def test_publish_social_needs_a_network(h):
    assert h.call("campaign_requests", "campaign-service", {"action": "PUBLISH_SOCIAL", "event_id": "d1", "networks": []}).reason == "NOTHING_TO_PUBLISH"


def test_social_test_should_need_saved_credentials(h):
    assert call(h, action="TEST_SOCIAL", network="telegram").reason == "NOT_CONFIGURED"
    assert call(h, action="TEST_SOCIAL", network="myspace").reason == "UNKNOWN_NETWORK"
