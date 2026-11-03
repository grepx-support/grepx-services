"""recognition-service: certificates per donor, shared/unique voucher codes, idempotency."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from grepx_config import load_config
from nexus_testkit import MemoryClient

from domain import allocate
from jobs import handle_event
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "recognition_requests", handle, cfg.live_criteria)
    for donor, state in (("ann", "attended"), ("bob", "attended"), ("cat", "no_show")):
        harness.seed("bookings", f"d1-{donor}", {"event_id": "d1", "person_id": donor, "state": state, "name": donor.title(), "email": f"{donor}@x.sg"})
    return harness


def complete(h, voucher=None):
    fields = {"status": "ACCEPTED", "state": "completed", "title": "Town Hall", "event_date": "2026-01-10", "voucher": voucher or {}}
    h.seed("events", "d1", {k: v for k, v in fields.items() if k != "status"})
    return handle_event(NexusApplication(MemoryClient(h.engine), "x"), Row("d1", fields), cfg)


def test_allocation():
    assert allocate({"codes": ["A", "B"]}, ["x", "y"]) == {"x": "A", "y": "B"}
    assert allocate({"code": "ALL"}, ["x", "y"]) == {"x": "ALL", "y": "ALL"}
    assert allocate({"codes": ["A"]}, ["x", "y"]) == {"x": "A"}  # codes ran out: y gets none (reported as short)


def test_completion_should_issue_once(h):
    assert complete(h, {"title": "Coffee", "codes": ["C1", "C2"]}) == {"certificates": 2, "vouchers": 2, "vouchers_short": 0}
    assert complete(h, {"title": "Coffee", "codes": ["C1", "C2"]}) == {"certificates": 0, "vouchers": 0, "vouchers_short": 0}
    assert sorted(v["code"] for v in h.read.accepted("vouchers")) == ["C1", "C2"]
    assert len(h.rows("notifications", template="certificate")) == 2


def test_issue_later_should_need_completed_event(h):
    assert h.call("recognition_requests", "recognition-service", {"action": "ISSUE", "event_id": "d1"}).reason == "UNKNOWN_EVENT"
    complete(h)
    v = h.call("recognition_requests", "recognition-service", {"action": "ISSUE", "event_id": "d1", "voucher": {"title": "Cake", "code": "CAKE"}})
    assert v.ok and v.fields["vouchers"] == 2
