# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""approval-service: a held request, the people who may decide emailed, four eyes, yes sends the held request on behalf
of the asker, no needs a reason and sends `otherwise`, the asker told; withdraw; one business never sees another's."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_ask
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "approval_requests"
THEN = {"table": "stock_requests", "service": "stock-service", "fields": {"action": "ADJUST", "delta": -2, "reason": "Stolen"}, "note_field": "note"}


def test_clean_ask():
    a = clean_ask({"kind": "Write_Off", "title": "  Write off 2  ", "perms": ["manage_business"], "amount": "4500", "then": THEN})
    assert (a["kind"], a["title"], a["amount"], a["then"]["service"]) == ("write_off", "Write off 2", 4500, "stock-service")
    for bad, reason in [({"kind": "x"}, "INVALID_KIND"), ({"kind": "ok_kind", "title": "no"}, "INVALID_TITLE"),
                        ({"kind": "ok_kind", "title": "fine", "perms": []}, "INVALID_REQUEST"),
                        ({"kind": "ok_kind", "title": "fine", "perms": ["p"], "then": {"table": "x", "service": "approval-service", "fields": {}}}, "INVALID_REQUEST")]:
        with pytest.raises(ValueError, match=reason):
            clean_ask(bad)


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("staff_roles", "gm.owner", {"name": "Owner", "perms": ["manage_business", "view_stock"]})
    harness.seed("staff_roles", "gm.warehouse", {"name": "Warehouse", "perms": ["view_stock", "adjust_stock"]})
    harness.seed("staff_roles", "zz.owner", {"name": "Owner", "perms": ["manage_business"]})
    for user, role, name in [("o1", "gm.owner", "Omar Owner"), ("o2", "gm.owner", "Priya Partner"), ("w1", "gm.warehouse", "Ravi Store"), ("z1", "zz.owner", "Zed")]:
        harness.seed("user_access", user, {"staff_role_id": role})
        harness.seed("people", user, {"name": name, "email": f"{user}@shop.test"})
    return harness


def call(h, who="w1", name="Ravi Store", tenant="gm", **fields):
    return h.call(T, "approval-service", {"tenant_id": tenant, "actor_id": who, "actor_name": name, **fields})


def test_ask_decide_and_send(h):
    r = call(h, action="ASK", kind="write_off", ref="adj-1", title="Write off 2 x Galaxy S25", amount=12000000, currency="INR",
             details=[{"k": "Reason", "v": "Stolen"}], perms=["manage_business"], then=THEN, link="#/approvals")
    assert r.ok, r.reason
    a = r.fields["approval"]
    assert r.fields["told"] == 2 and a["state"] == "pending" and a["by_email"] == "w1@shop.test"
    mails = [n for n in h.rows("notifications") if n.get("template") == "approval_request"]
    assert sorted(n["recipient"] for n in mails) == ["o1@shop.test", "o2@shop.test"] and mails[0]["values"]["amount"] == "INR 120,000.00"
    again = call(h, action="ASK", kind="write_off", ref="adj-1", title="Write off 2 x Galaxy S25", perms=["manage_business"], then=THEN)
    assert again.fields["approval"]["approval_id"] == a["approval_id"]                       # asked twice: still one
    key = a["approval_id"]
    assert call(h, action="DECIDE", approval_id=key, approve=True).reason == "NOT_ALLOWED"     # warehouse staff can't
    assert call(h, who="o1", name="Omar Owner", action="DECIDE", approval_id=key, approve=False).reason == "NOTE_REQUIRED"
    assert call(h, who="z1", tenant="zz", action="DECIDE", approval_id=key, approve=True).reason == "UNKNOWN_APPROVAL"
    ok = call(h, who="o1", name="Omar Owner", action="DECIDE", approval_id=key, approve=True, note="CCTV checked")
    assert ok.ok and ok.fields["approval"]["state"] == "approved"
    sent = h.rows("stock_requests")[-1]
    assert (sent["action"], sent["actor_id"], sent["note"], sent["approved_by"], sent["tenant_id"]) == ("ADJUST", "w1", "CCTV checked", "Omar Owner", "gm")
    told = [n for n in h.rows("notifications") if n.get("template") == "approval_decided"]
    assert told[0]["recipient"] == "w1@shop.test" and told[0]["values"]["decision"] == "approved"
    assert call(h, who="o2", name="Priya", action="DECIDE", approval_id=key, approve=True).reason == "ALREADY_DECIDED"


def test_four_eyes_withdraw_and_no(h):
    mine = call(h, who="o1", name="Omar Owner", action="ASK", kind="purchase_order", ref="po1", title="PO-0007 Redington", perms=["manage_business"],
                otherwise={"table": "purchase_requests", "service": "purchase-service", "fields": {"action": "APPROVE", "po_id": "po1", "approve": False},
                           "note_field": "note"}).fields["approval"]
    assert call(h, who="o1", name="Omar Owner", action="DECIDE", approval_id=mine["approval_id"], approve=True).reason == "OWN_REQUEST"
    no = call(h, who="o2", name="Priya", action="DECIDE", approval_id=mine["approval_id"], approve=False, note="Too many")
    assert no.fields["approval"]["state"] == "rejected" and h.rows("purchase_requests")[-1]["note"] == "Too many"
    w = call(h, action="ASK", kind="price_change", title="New prices for 4 models", perms=["manage_business"]).fields["approval"]
    assert call(h, who="o1", name="Omar", action="WITHDRAW", approval_id=w["approval_id"]).reason == "NOT_YOURS"
    assert call(h, action="WITHDRAW", approval_id=w["approval_id"]).fields["approval"]["state"] == "withdrawn"
    assert call(h, tenant="zz", who="z1", action="ASK", kind="write_off", title="x y z", perms=["adjust_stock"]).reason == "NO_DECIDERS"
