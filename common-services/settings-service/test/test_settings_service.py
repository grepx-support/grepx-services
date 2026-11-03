# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from domain import valid_name
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, "settings_requests", handle, cfg.live_criteria)


def call(h, **f):
    return h.call("settings_requests", "settings-service", f)


def test_names():
    assert valid_name("SMTP_HOST") and valid_name("auto.welcome.channels") and not valid_name("bad name") and not valid_name("")


def test_set_then_delete(h):
    assert call(h, action="SET", name="SMTP_HOST", value="smtp.example.com").ok
    assert h.read.accepted_one("app_settings", "SMTP_HOST")["value"] == "smtp.example.com"
    assert call(h, action="DELETE", name="SMTP_HOST").ok
    assert h.read.accepted_one("app_settings", "SMTP_HOST") is None


def test_sealed_values_are_stored_as_sent_and_never_echoed(h):
    v = call(h, action="SET", name="SMTP_PASS", value="enc:gAAAAA-sealed", secret=True)
    assert v.ok and v.fields["value"] == ""
    row = h.read.accepted_one("app_settings", "SMTP_PASS")
    assert (row["value"], row["secret"]) == ("enc:gAAAAA-sealed", True)


def test_invalid_name_is_rejected(h):
    assert call(h, action="SET", name="no spaces", value="x").reason == "INVALID_NAME"
