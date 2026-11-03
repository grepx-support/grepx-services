"""notification-service: rendering, admin settings, channel fallback and failures."""
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_config import load_config

from channels import Channel, ChannelFactory
from domain import render
from routes import handle
from routes.send import Deps

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


class Boom(Channel):
    name = "sms"

    def configured(self):
        return True

    def send(self, *a, **k):
        raise OSError("provider down")


class Sink(Channel):
    name = "email"
    sent: list = []

    def configured(self):
        return True

    def send(self, recipient, subject, body, html=None):
        Sink.sent.append((recipient, subject, body))

    def check(self):
        return "Signed in"


@pytest.fixture()
def h():
    Sink.sent = []
    Deps.channels = ChannelFactory([Sink(), Boom()])
    harness = ServiceHarness().add(cfg, "notifications", handle, cfg.live_criteria)
    harness.seed("message_templates", "welcome", {"placeholders": ["first_name"], "channels": ["email", "sms", "whatsapp"],
                                                  "bodies": {"subject": "Welcome {first_name}", "text": "Hi {first_name}, see https://x.sg"}})
    return harness


def send(h, channel="email", template="welcome", **extra):
    return h.call("notifications", "notification-service", {"action": "SEND", "template": template, "channel": channel,
                                                              "recipient": "a@b.sg", "values": {"first_name": "Ann"}, **extra})


def test_email_should_render_and_send(h):
    v = send(h)
    assert v.fields["delivery"] == "SENT" and Sink.sent[0][1] == "Welcome Ann"


def test_unconfigured_channel_should_be_logged(h):
    assert send(h, channel="whatsapp").fields["delivery"] == "LOGGED"


def test_provider_error_should_be_failed_not_crash(h):
    v = send(h, channel="sms")
    assert v.ok and v.fields["delivery"] == "FAILED" and "provider down" in v.fields["error"]


def test_disabled_auto_message_should_be_skipped(h):
    h.seed("message_settings", "welcome", {"enabled": False, "channels": ["email"]})
    assert send(h).fields["delivery"] == "SKIPPED"


def test_unknown_template_should_reject(h):
    assert send(h, template="nope").reason == "UNKNOWN_TEMPLATE"


def test_custom_wording_should_win_and_escape_html():
    msg = render({"bodies": {"text": "x"}}, {"text": "Hi {first_name} <b>\n\nhttp://a.sg {unknown}"}, "email", {"first_name": "Ann"}, "Org")
    assert msg.body.startswith("Hi Ann <b>") and "&lt;b&gt;" in msg.html and '<a href="http://a.sg">' in msg.html and "{unknown}" in msg.body


def test_channel_test_should_report_sign_in_or_provider_error(h):
    test = lambda name: h.call("notifications", "notification-service", {"action": "TEST_CHANNEL", "channel": name})  # noqa: E731
    assert test("email").fields["message"] == "Signed in"
    assert test("sms").reason == "CHECK_FAILED"          # Boom has no connection test
    assert test("whatsapp").reason == "NOT_CONFIGURED"
