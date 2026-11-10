# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""lead-service: website enquiries kept as leads, bots turned away, follow-up history."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_lead
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


def test_clean_lead():
    lead = clean_lead({"name": " Ana  B ", "email": "ANA@Taco.test", "company": "Taco Co", "message": "hi"})
    assert (lead["name"], lead["email"], lead["kind"]) == ("Ana B", "ana@taco.test", "demo")
    for bad, reason in (({"name": "A", "email": "a@b.co"}, "INVALID_NAME"), ({"name": "Ana", "email": "nope"}, "INVALID_EMAIL"),
                        ({"name": "Ana", "email": "a@b.co", "website": "http://spam"}, "SPAM")):
        with pytest.raises(ValueError, match=reason):
            clean_lead(bad)


def test_a_lead_is_kept_announced_and_followed_up(monkeypatch):
    monkeypatch.setenv("LEADS_NOTIFY_EMAIL", "sales@grepx.test")
    h = ServiceHarness().add(cfg, "lead_requests", handle, cfg.live_criteria)
    v = h.call("lead_requests", "lead-service", {"action": "SUBMIT", "name": "Ana", "email": "ana@taco.test", "company": "Taco Co"})
    assert v.ok and h.rows("leads")[0]["stage"] == "new"
    note = h.rows("notifications")[0]
    assert (note["recipient"], note["template"], note["values"]["company"]) == ("sales@grepx.test", "demo_request", "Taco Co")
    done = h.call("lead_requests", "lead-service", {"action": "SET_STATUS", "lead_id": v.fields["lead_id"], "stage": "contacted",
                                                    "note": "Called", "actor_name": "Ops"})
    assert done.fields["lead"]["history"][0]["note"] == "Called"
    assert h.call("lead_requests", "lead-service", {"action": "SET_STATUS", "lead_id": v.fields["lead_id"], "stage": "maybe"}).reason == "INVALID_STATUS"
