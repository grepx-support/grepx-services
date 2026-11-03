"""template-service: seeding built-ins, saving admin wording, placeholder safety."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "templates", handle, cfg.live_criteria)
    harness.call("templates", "template-service", {"action": "SEED", "template_key": "welcome", "placeholders": ["first_name", "link"],
                                                   "bodies": {"text": "Hi {first_name}"}})
    return harness


def call(h, **f):
    return h.call("templates", "template-service", f)


def test_save_should_store_settings(h):
    assert call(h, action="SAVE", template_key="welcome", enabled=False, channels=["email"], text="Yo {first_name}").ok
    row = h.read.accepted_one("message_settings", "welcome")
    assert row["enabled"] is False and row["channels"] == ["email"]


def test_unknown_placeholder_should_reject(h):
    v = call(h, action="SAVE", template_key="welcome", text="Hi {password}")
    assert v.reason == "UNKNOWN_PLACEHOLDER" and v.fields["detail"] == "password"


def test_unknown_template_should_reject(h):
    assert call(h, action="SAVE", template_key="nope").reason == "UNKNOWN_TEMPLATE"


def test_reset_should_remove_settings(h):
    call(h, action="SAVE", template_key="welcome", text="x")
    call(h, action="RESET", template_key="welcome")
    assert h.read.accepted_one("message_settings", "welcome") is None
