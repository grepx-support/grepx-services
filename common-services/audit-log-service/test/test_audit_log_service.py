"""audit-log-service: records what grepx_audit writes."""
from pathlib import Path

from grepx_audit import write_audit
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


def test_write_audit_should_be_recorded():
    h = ServiceHarness().add(cfg, "audit_log", handle, cfg.live_criteria)
    key = write_audit(h.client, from_service="event-service", actor_user_id="u1", action="CREATE", entity_type="drive", entity_id="d1")
    assert h.rows("audit_log", transaction_id=key)[0]["status"] == "ACCEPTED"
