"""referral-service: points per friend who joins and more once they convert (weights and tables from config); referrer is told."""
from pathlib import Path

from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from grepx_config import load_config
from nexus_testkit import MemoryClient

from jobs import handle_conversion, handle_person

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
cfg.update({"person": {"table": "people"}, "referral": {"join_points": 1, "convert_points": 2, "conversion": {"table": "conversions", "field": "count"}}})


def test_points_should_follow_joins_and_donations():
    h = ServiceHarness()
    app = NexusApplication(MemoryClient(h.engine), "x")
    h.seed("people", "ann", {"name": "Ann Tan", "email": "ann@x.sg"})
    h.seed("people", "bob", {"name": "Bob Lim", "referred_by": "ann"})
    assert handle_person(app, Row("bob", {"status": "ACCEPTED", "referred_by": "ann", "name": "Bob Lim"}), cfg) == "scored"
    assert h.read.accepted_one("referral_scores", "ann")["points"] == 1
    h.seed("conversions", "bob", {"count": 1})
    handle_conversion(app, Row("bob", {"status": "ACCEPTED", "count": 1}), cfg)
    assert h.read.accepted_one("referral_scores", "ann")["points"] == 3
    assert h.rows("notifications")[0]["values"]["friend"] == "Bob"


def test_unreferred_donor_should_be_ignored():
    h = ServiceHarness()
    app = NexusApplication(MemoryClient(h.engine), "x")
    assert handle_person(app, Row("x", {"status": "ACCEPTED", "referred_by": ""}), cfg) == "ignored"
