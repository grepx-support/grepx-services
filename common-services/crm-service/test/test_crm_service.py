# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""crm-service: contacts and companies, deals dragged across stages, won / lost, activities and the agenda, a contact's
timeline, the board with stale deals, insights; another business sees nothing."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_stages, move
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "crm_requests", handle, cfg.live_criteria)


def call(h, tenant="b1", **f):
    return h.call("crm_requests", "crm-service", {"tenant_id": tenant, "today": "2026-11-15", **f})


def test_rules():
    assert [s["stage_id"] for s in clean_stages([{"name": "Hot lead"}, {"name": "Demo booked", "chance": 140}])] == ["hot-lead", "demo-booked"]
    with pytest.raises(ValueError):
        clean_stages([{"name": "A"}, {"name": "a"}])
    deals = [{"deal_id": x, "stage": s, "state": "open", "order": n} for n, (x, s) in enumerate([("a", "new"), ("b", "new"), ("c", "quote")])]
    assert [d["deal_id"] for d in move(deals, "a", "quote", 1)] == ["c", "a"]


def test_contacts_deals_activities_and_views(h):
    acme = call(h, action="SAVE_CONTACT", kind="company", name="Acme Retail", tax_number="29ABCDE1234F1Z5").fields["contact"]
    ravi = call(h, action="SAVE_CONTACT", name="Ravi Kumar", email="RAVI@acme.in", company_id=acme["contact_id"], tags=["Dealer", "dealer "]).fields["contact"]
    assert ravi["email"] == "ravi@acme.in" and ravi["tags"] == ["dealer"]
    assert call(h, action="SAVE_CONTACT", name="X", email="nope").reason == "INVALID_EMAIL"
    deal = call(h, action="SAVE_DEAL", title="50 laptops for Acme", value="45000", contact_id=ravi["contact_id"], company_id=acme["contact_id"],
                expected_close="2026-12-10", source="Referral", owner_name="Sam").fields["deal"]
    other = call(h, action="SAVE_DEAL", title="Printers", value=8000, stage="quote").fields["deal"]
    assert deal["stage"] == "new" and deal["value"] == 4500000
    moved = call(h, action="MOVE_DEAL", deal_id=deal["deal_id"], stage="quote", index=0)
    assert moved.fields["column"] == [deal["deal_id"], other["deal_id"]]
    call(h, action="LOG_ACTIVITY", kind="call", subject="Talked prices", deal_id=deal["deal_id"])
    task = call(h, action="LOG_ACTIVITY", kind="task", subject="Send quote", contact_id=ravi["contact_id"], due="2026-11-14").fields["activity"]
    assert call(h, action="AGENDA").fields["overdue"][0]["contact_name"] == "Ravi Kumar"
    call(h, action="COMPLETE_ACTIVITY", activity_id=task["activity_id"], outcome="sent")
    assert call(h, action="AGENDA").fields["overdue"] == []
    tl = call(h, action="TIMELINE", contact_id=acme["contact_id"]).fields
    assert [p["name"] for p in tl["people"]] == ["Ravi Kumar"] and len(tl["activities"]) == 2 and tl["deals"][0]["title"] == "50 laptops for Acme"
    board = call(h, action="BOARD").fields
    quote = next(s for s in board["stages"] if s["stage_id"] == "quote")
    assert quote["count"] == 2 and quote["weighted"] == (4500000 + 800000) // 2
    assert call(h, action="CLOSE_DEAL", deal_id=other["deal_id"], won=False).reason == "REASON_NEEDED"
    call(h, action="CLOSE_DEAL", deal_id=other["deal_id"], won=False, reason="Price")
    call(h, action="CLOSE_DEAL", deal_id=deal["deal_id"], won=True)
    ins = call(h, action="INSIGHTS").fields["insights"]
    assert ins["win_rate"] == 50.0 and ins["won"]["value"] == 4500000 and ins["lost_reasons"] == [{"reason": "Price", "count": 1}]
    assert call(h, action="REOPEN_DEAL", deal_id=deal["deal_id"]).fields["deal"]["state"] == "open"
    assert call(h, tenant="b2", action="TIMELINE", contact_id=acme["contact_id"]).reason == "UNKNOWN_CONTACT"
    assert call(h, tenant="b2", action="BOARD").fields["open_value"] == 0
    stages = call(h, action="SAVE_PIPELINE", stages=[{"name": "Lead", "chance": 10}, {"name": "Won soon", "chance": 90}]).fields["stages"]
    assert [s["stage_id"] for s in stages] == ["lead", "won-soon"]
