# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""employee-service: records, sites, pay basis, documents and their expiry, leaving; one business never sees another's."""
from datetime import date
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_employee, needing_action
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "employee_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("employee_requests", "employee-service", {"tenant_id": "b1", **f})


def test_rules():
    e = clean_employee({"name": " Meera  Iyer ", "email": "M@X.com", "sites": ["k1", "s2"], "home_site": "s3",
                        "pay": {"basis": "hourly", "rate": "250.555"}})
    assert e["name"] == "Meera Iyer" and e["email"] == "m@x.com" and e["sites"] == ["s3", "k1", "s2"] and e["pay"]["rate"] == 250.56
    for bad, reason in (({"name": "A"}, "INVALID_NAME"), ({"name": "Ann", "email": "nope"}, "INVALID_EMAIL"),
                        ({"name": "Ann", "pay": {"basis": "weekly"}}, "INVALID_PAY"),
                        ({"name": "Ann", "start_date": "2026-05-01", "end_date": "2026-04-01"}, "INVALID_DATE")):
        with pytest.raises(ValueError, match=reason):
            clean_employee(bad)


def test_employees_documents_and_leaving(h):
    e = call(h, action="SAVE", name="Meera Iyer", email="meera@x.com", position="Sous chef", home_site="k1", sites=["s1"],
             start_date="2025-01-10", pay={"basis": "monthly", "rate": 45000})
    assert e.ok and e.fields["employee"]["sites"] == ["k1", "s1"]
    eid = e.fields["employee"]["employee_id"]
    assert call(h, action="SAVE", name="Other", email="MEERA@x.com").reason == "DUPLICATE_EMAIL"
    changed = call(h, action="SAVE", employee_id=eid, position="Head chef").fields["employee"]
    assert changed["position"] == "Head chef" and changed["pay"]["rate"] == 45000 and changed["email"] == "meera@x.com"
    doc = call(h, action="SET_DOCUMENT", employee_id=eid, document={"kind": "Food handler licence", "expires_on": "2020-01-01"})
    did = doc.fields["employee"]["documents"][0]["doc_id"]
    call(h, action="SET_DOCUMENT", employee_id=eid, document={"doc_id": did, "kind": "Food handler licence", "expires_on": "2099-01-01"})
    call(h, action="SET_DOCUMENT", employee_id=eid, document={"kind": "Visa", "expires_on": "2026-01-20"})
    row = h.read.accepted_one("employees", eid)
    assert len(row["documents"]) == 2
    team = call(h, action="TEAM", site_id="s1").fields
    assert team["team"][0]["name"] == "Meera Iyer" and {d["state"] for d in team["team"][0]["documents"]} <= {"valid", "expiring", "expired"}
    assert call(h, action="TEAM", site_id="zz").fields["team"] == []
    due = needing_action([row], date(2026, 1, 1))
    assert [(d["kind"], d["state"]) for d in due] == [("Visa", "expiring")]
    assert call(h, action="SET_DOCUMENT", employee_id=eid, document={"kind": ""}).reason == "INVALID_DOCUMENT"
    assert len(call(h, action="REMOVE_DOCUMENT", employee_id=eid, doc_id=did).fields["employee"]["documents"]) == 1
    # another business cannot see or change this person
    assert h.call("employee_requests", "employee-service", {"tenant_id": "b2", "action": "SAVE", "employee_id": eid, "name": "X"}).reason == "UNKNOWN_EMPLOYEE"
    assert h.call("employee_requests", "employee-service", {"action": "SAVE", "name": "Y Z"}).reason == "MISSING_TENANT"
    gone = call(h, action="END", employee_id=eid, end_date="2026-01-31", reason="Moved city")
    assert gone.ok and gone.fields["employee"]["active"] is False and gone.fields["employee"]["end_reason"] == "Moved city"
    assert call(h, action="END", employee_id=eid).reason == "ALREADY_ENDED"
    assert call(h, action="SAVE", name="New Meera", email="meera@x.com").ok          # the email is free again
