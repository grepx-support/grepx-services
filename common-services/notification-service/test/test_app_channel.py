# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The app channel: a message to a person is kept for their bell and pushed to each device they registered (Web Push);
a broken subscription is refused; the VAPID pair is made once and its public key handed out; MARK_SEEN marks the bell
read; a device switched off gets no more pushes; a failed push never fails the message."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from channels import AppChannel, ChannelFactory
from routes import handle
from routes.send import Deps

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
SUB = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc", "keys": {"p256dh": "BPkey", "auth": "authkey"}}


class Pushes(AppChannel):
    sent: list = []

    def send(self, recipient, subject, body, html=None, devices=None, vapid=None, link="", **_):
        Pushes.sent.append({"to": recipient, "devices": len(devices or []), "has_key": bool(vapid and vapid.get("private")), "link": link})


@pytest.fixture()
def h():
    Pushes.sent = []
    Deps.channels = ChannelFactory([Pushes()])
    harness = ServiceHarness().add(cfg, "notifications", handle, cfg.live_criteria)
    harness.seed("message_templates", "job_assigned", {"placeholders": ["number"], "channels": ["app", "sms"],
                                                       "bodies": {"subject": "New job {number}", "text": "You have job {number}"}})
    return harness


def call(h, **f):
    return h.call("notifications", "notification-service", f)


def test_app_messages_and_push(h):
    key = call(h, action="PUSH_KEY").fields["public_key"]
    assert len(key) > 80 and call(h, action="PUSH_KEY").fields["public_key"] == key                 # made once
    assert call(h, action="REGISTER_DEVICE", user_id="u1", subscription={"endpoint": "http://x"}).reason == "BAD_SUBSCRIPTION"
    assert call(h, action="REGISTER_DEVICE", subscription=SUB).reason == "MISSING_USER"
    assert call(h, action="REGISTER_DEVICE", user_id="u1", tenant_id="ag", subscription=SUB, label="Azman's phone").ok
    sent = call(h, action="SEND", template="job_assigned", channel="app", recipient="u1", values={"number": "J-00009", "link": "#/my-jobs"}, tenant_id="ag")
    assert sent.fields["delivery"] == "SENT" and sent.fields["subject"] == "New job J-00009"
    assert Pushes.sent == [{"to": "u1", "devices": 1, "has_key": True, "link": "#/my-jobs"}]
    assert call(h, action="FORGET_DEVICE", user_id="u1", endpoint=SUB["endpoint"]).fields["forgotten"]
    call(h, action="SEND", template="job_assigned", channel="app", recipient="u1", values={"number": "J-00010"}, tenant_id="ag")
    assert Pushes.sent[-1]["devices"] == 0
    assert call(h, action="MARK_SEEN", user_id="u1").fields["seen_until"]


def test_a_failed_push_never_fails_the_message():
    AppChannel().send("u1", "Hi", "Body", None, devices=[{"subscription": SUB}], vapid={"private": "not a key"})       # logs, no raise
