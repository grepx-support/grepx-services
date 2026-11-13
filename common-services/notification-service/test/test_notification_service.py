# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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


def send(h, channel="email", template="welcome", key=None, **extra):
    return h.call("notifications", "notification-service", {"action": "SEND", "template": template, "channel": channel,
                                                              "recipient": "a@b.sg", "values": {"first_name": "Ann"}, **extra}, key)


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


# ---------------- providers, attachments, test messages ----------------
class Files(Channel):
    name = "email"
    got: list = []

    def configured(self):
        return True

    def send(self, recipient, subject, body, html=None, attachments=None):
        Files.got.append(attachments)


def test_whatsapp_provider_is_chosen_by_setting_or_keys():
    from channels import MetaWhatsAppChannel, whatsapp
    meta = {"WHATSAPP_TOKEN": "t", "WHATSAPP_PHONE_ID": "123"}
    twilio = {"TWILIO_SID": "s", "TWILIO_TOKEN": "t", "TWILIO_WHATSAPP_FROM": "+65"}
    assert isinstance(whatsapp(meta), MetaWhatsAppChannel)
    assert not isinstance(whatsapp(twilio), MetaWhatsAppChannel)
    assert not isinstance(whatsapp({**meta, **twilio, "WHATSAPP_PROVIDER": "twilio"}), MetaWhatsAppChannel)
    assert isinstance(whatsapp({**meta, **twilio, "WHATSAPP_PROVIDER": "META"}), MetaWhatsAppChannel)
    assert MetaWhatsAppChannel.payload("+91 98000 00001", "Hi")["to"] == "919800000001"


def test_email_carries_attachments():
    from channels import SmtpEmailChannel
    msg = SmtpEmailChannel({"SMTP_HOST": "h", "SMTP_FROM": "a@b.sg"}).build("c@d.sg", "PO", "see attached", None,
                                                                        [{"name": "PO-0001.pdf", "mime": "application/pdf", "data": b"%PDF-1.4"}])
    parts = [p for p in msg.iter_attachments()]
    assert [(p.get_filename(), p.get_content_type(), p.get_content()) for p in parts] == [("PO-0001.pdf", "application/pdf", b"%PDF-1.4")]


def test_send_passes_files_and_refuses_huge_ones(h):
    import base64
    Files.got = []
    Deps.channels = ChannelFactory([Files()])
    pdf = {"name": "a.pdf", "mime": "application/pdf", "data_b64": base64.b64encode(b"%PDF").decode()}
    assert send(h, attachments=[pdf]).fields["delivery"] == "SENT"
    assert Files.got == [[{"name": "a.pdf", "mime": "application/pdf", "data": b"%PDF"}]]
    big = {"name": "b.pdf", "data_b64": base64.b64encode(b"x" * (8 * 1024 * 1024 + 1)).decode()}
    assert send(h, attachments=[big]).reason == "ATTACHMENT_TOO_LARGE"


def test_test_send(h):
    v = h.call("notifications", "notification-service", {"action": "TEST_SEND", "channel": "email", "recipient": "a@b.sg"})
    assert v.fields["delivery"] == "SENT" and Sink.sent[-1][1].startswith("Test message from")
    v = h.call("notifications", "notification-service", {"action": "TEST_SEND", "channel": "sms", "recipient": "+6591234567"})
    assert v.fields["delivery"] == "FAILED" and "provider down" in v.fields["error"]
    assert h.call("notifications", "notification-service", {"action": "TEST_SEND", "channel": "pigeon", "recipient": "x"}).reason == "UNKNOWN_CHANNEL"


# ---------------- a business's own settings; trying failed sends again ----------------
def test_a_business_setting_wins_over_the_default(h):
    h.seed("message_settings", "welcome", {"enabled": True, "channels": ["email"]})
    h.seed("message_settings", "hft:welcome", {"enabled": False, "channels": ["email"]})
    assert send(h, tenant_id="hft").fields["delivery"] == "SKIPPED"
    assert send(h, tenant_id="other").fields["delivery"] == "SENT"


def test_retry_waits_grow_and_stop_after_four_tries():
    from datetime import datetime, timezone
    from domain import retry
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    row = {"_key": "k", "action": "SEND", "delivery": "FAILED", "sent_at": "2026-01-01T11:50:00+00:00", "template": "t", "x": 1}
    never = lambda key: False  # noqa: E731
    assert retry.due([row], now, never) == [row]                                     # 10 min > 5 min wait
    assert retry.due([{**row, "attempt": 2}], now, never) == []                        # needs 30 min
    assert retry.due([{**row, "attempt": 4}], now, never) == []                        # gave up
    assert retry.due([row], now, lambda key: key == "k~2") == []                       # already tried again
    assert retry.due([{**row, "action": "TEST_SEND"}], now, never) == []
    nxt = retry.again({**row, "attempt": 2, "retry_of": "k"})
    assert nxt["attempt"] == 3 and nxt["retry_of"] == "k" and "x" not in nxt and retry.next_key({**row, "attempt": 2, "retry_of": "k"}) == "k~3"


def test_try_again_now_and_the_job(h):
    from datetime import datetime, timedelta, timezone
    from jobs import handle_tick
    from nexus_api import NexusApplication, Row
    from nexus_testkit import MemoryClient
    first = send(h, channel="sms", key="n1", tenant_id="hft")
    assert first.fields["delivery"] == "FAILED" and first.fields["attempt"] == 1
    retry = lambda **f: h.call("notifications", "notification-service", {"action": "RETRY", **f})  # noqa: E731
    assert retry(key="n1", tenant_id="other").reason == "NOT_FAILED"                   # not that business's
    assert retry(key="n1", tenant_id="hft").fields["key"] == "n1~2"
    assert retry(key="n1", tenant_id="hft").reason == "ALREADY_RETRIED"
    second = h.read.accepted_one("notifications", "n1~2")
    assert second["attempt"] == 2 and second["retry_of"] == "n1" and second["delivery"] == "FAILED"
    app = NexusApplication(MemoryClient(h.engine), "x")
    tick = lambda key, when: handle_tick(app, Row(key, {"job": "notify-retry", "status": "NEW"}), cfg, when)  # noqa: E731
    assert tick("t1", datetime.now(timezone.utc)) == 0                                  # too soon
    assert tick("t2", datetime.now(timezone.utc) + timedelta(minutes=31)) == 1          # n1~2 -> n1~3
    h.settle()
    assert h.read.accepted_one("notifications", "n1~3")["attempt"] == 3
