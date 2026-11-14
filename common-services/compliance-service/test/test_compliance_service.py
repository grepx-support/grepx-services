# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""compliance-service: readings with safe ranges, checklists, corrective action on failures, what is due, history."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_point, due, judge
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "compliance_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("compliance_requests", "compliance-service", {"tenant_id": "b1", "actor_name": "Meera", **f})


def test_rules():
    fridge = clean_point({"name": "Walk-in fridge", "unit": "°C", "min": 0, "max": 5, "every": "twice_daily"})
    assert judge(fridge, {"value": "4.5"})["ok"] and not judge(fridge, {"value": 7})["ok"]
    freezer = clean_point({"name": "Freezer", "max": -18})
    assert judge(freezer, {"value": -20})["ok"] and not judge(freezer, {"value": -12})["ok"]
    for bad in ({"name": ""}, {"name": "X"}, {"name": "X", "min": 5, "max": 1}, {"name": "X", "kind": "checklist"}):
        with pytest.raises(ValueError):
            clean_point(bad)
    opening = clean_point({"name": "Opening", "kind": "checklist", "questions": ["Hands washed", "Surfaces sanitised"]})
    assert judge(opening, {"answers": {"Hands washed": True, "Surfaces sanitised": False}})["failed"] == ["Surfaces sanitised"]
    with pytest.raises(ValueError):
        judge(opening, {"answers": {"Hands washed": True}})
    assert due(fridge, 1, 1) == 1 and due({"every": "weekly"}, 0, 1) == 0


def test_a_day_of_checks(h):
    fridge = call(h, action="SAVE_POINT", site_id="k1", name="Walk-in fridge", unit="°C", min=0, max=5, every="twice_daily", group="Temperatures").fields["point"]
    opening = call(h, action="SAVE_POINT", site_id="k1", name="Opening checks", kind="checklist", questions=["Hands washed", "Pest free"]).fields["point"]
    assert call(h, action="SAVE_POINT", name="No site", max=5).reason == "MISSING_SITE"
    assert call(h, action="RECORD", point_id=fridge["point_id"], value=3, at="2026-11-16T08:00").fields["record"]["ok"]
    assert call(h, action="RECORD", point_id=fridge["point_id"], value=9, at="2026-11-16T15:00").reason == "ACTION_NEEDED"
    hot = call(h, action="RECORD", point_id=fridge["point_id"], value=9, at="2026-11-16T15:00", action_taken="Moved stock, called technician")
    assert hot.fields["record"]["ok"] is False and hot.fields["record"]["by"] == "Meera"
    assert call(h, action="RECORD", point_id=opening["point_id"], answers={"Hands washed": True, "Pest free": True}, at="2026-11-16T07:00").ok
    day = call(h, action="DAY", site_id="k1", date="2026-11-16").fields
    assert (day["due"], day["failed"]) == (0, 1) and {p["name"]: len(p["today"]) for p in day["points"]} == {"Walk-in fridge": 2, "Opening checks": 1}
    assert call(h, action="DAY", site_id="k1", date="2026-11-17").fields["due"] == 3
    hist = call(h, action="HISTORY", first="2026-11-01", last="2026-11-30").fields
    assert hist["total"] == 3 and hist["failed"] == 1
    assert call(h, action="REMOVE_POINT", point_id=opening["point_id"]).ok
    assert len(call(h, action="DAY", site_id="k1", date="2026-11-17").fields["points"]) == 1
    assert h.call("compliance_requests", "compliance-service", {"tenant_id": "b2", "action": "RECORD", "point_id": fridge["point_id"], "value": 1}).reason == "UNKNOWN_POINT"
