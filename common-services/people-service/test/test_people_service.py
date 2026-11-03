# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""people-service: contact validation, unique email, referral codes, product fields through a profile plugin."""
import sys
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from domain import ProfileError, clean_contact
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
cfg.update({"plugins": {}})
ANN = {"name": "Ann Tan", "email": "Ann@x.sg", "phone": "9123 4567"}


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "people_requests", handle, cfg.live_criteria)


def create(h, **f):
    return h.call("people_requests", "people-service", {"action": "CREATE", **ANN, **f})


def test_contact_rules():
    assert clean_contact(ANN) == {"name": "Ann Tan", "email": "ann@x.sg", "phone": "+6591234567"}
    for bad, reason in (({"name": "A1"}, "INVALID_NAME"), ({"email": "x"}, "INVALID_EMAIL"), ({"phone": "12"}, "INVALID_PHONE")):
        with pytest.raises(ProfileError, match=reason):
            clean_contact({**ANN, **bad})


def test_create_welcomes_and_keeps_email_unique(h):
    v = create(h)
    person = h.read.accepted_one("people", v.fields["person_id"])
    assert (person["email"], person["phone"], person["ref_code"]) == ("ann@x.sg", "+6591234567", v.fields["ref_code"])
    assert {n["template"] for n in h.rows("notifications")} == {"welcome"}
    assert create(h, email="ANN@x.sg").reason == "EMAIL_TAKEN"


def test_invite_code_records_referrer_and_walk_in_needs_no_email(h):
    ann = create(h).fields
    bob = create(h, name="Bob Lim", email="bob@x.sg", invite_code=ann["ref_code"]).fields["person_id"]
    assert h.read.accepted_one("people", bob)["referred_by"] == ann["person_id"]
    walk = create(h, name="Walt Walker", email="", allow_no_email=True, source="walkin")
    assert walk.ok and h.read.accepted_one("people", walk.fields["person_id"])["email"].endswith("@no-email.local")


def test_update_photo_and_calendar_token(h):
    pid = create(h).fields["person_id"]
    token = h.read.accepted_one("people", pid)["cal_token"]
    assert h.call("people_requests", "people-service", {"action": "UPDATE", "person_id": pid, "name": "Ann Lee"}).ok
    assert h.call("people_requests", "people-service", {"action": "SET_PHOTO", "person_id": pid, "photo_id": "m1"}).ok
    assert h.call("people_requests", "people-service", {"action": "RESET_CAL_TOKEN", "person_id": pid}).ok
    person = h.read.accepted_one("people", pid)
    assert (person["name"], person["photo_id"]) == ("Ann Lee", "m1") and person["cal_token"] != token
    assert h.call("people_requests", "people-service", {"action": "UPDATE", "person_id": "nope"}).reason == "UNKNOWN_PERSON"


def test_profile_plugin_adds_product_fields(h, tmp_path):
    (tmp_path / "club_profile.py").write_text(
        "FIELDS = ('team',)\n"
        "def clean(raw, partial):\n"
        "    if not partial and not raw.get('team'):\n"
        "        raise ValueError('MISSING_TEAM')\n"
        "    return {'team': raw['team'].upper()} if raw.get('team') else {}\n")
    cfg.update({"workspace": str(tmp_path), "plugins": {"path": ".", "profile": "club_profile"}})
    try:
        assert create(h).reason == "MISSING_TEAM"
        pid = create(h, team="red").fields["person_id"]
        assert h.read.accepted_one("people", pid)["team"] == "RED"
    finally:
        cfg.update({"plugins": {}})
        sys.modules.pop("club_profile", None)
