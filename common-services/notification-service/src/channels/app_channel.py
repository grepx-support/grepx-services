# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The app channel: the message is kept as the person's in-app inbox (the bell - the notification row itself), and
pushed to each of their phones / browsers that allowed notifications (Web Push, VAPID - pywebpush, MPL-2.0). A push
that fails never fails the message: the bell still has it. Recipient: the person's user id."""
from __future__ import annotations

import json
import logging

from .base import Channel

log = logging.getLogger("app-channel")


class AppChannel(Channel):
    name = "app"

    def configured(self) -> bool:
        return True

    def send(self, recipient: str, subject: str, body: str, html: str | None, devices: list | None = None, vapid: dict | None = None,
             link: str = "", **_) -> None:
        if not devices or not vapid:
            return
        try:
            from pywebpush import WebPushException, webpush   # noqa: PLC0415 - optional: without it the bell still works
        except ImportError:
            log.info("pywebpush is not installed: in-app only")
            return
        payload = json.dumps({"title": subject or "New message", "body": body[:300], "url": link or "/"})
        for d in devices:
            try:
                webpush(subscription_info=d["subscription"], data=payload, vapid_private_key=vapid["private"],
                        vapid_claims={"sub": vapid.get("subject") or "mailto:support@grepx.sg"}, ttl=3600)
            except WebPushException as exc:          # gone / expired devices are skipped; the inbox has the message
                log.info("push to %s failed: %s", d.get("label", "device"), str(exc)[:120])
            except Exception as exc:                 # noqa: BLE001
                log.info("push failed: %s", str(exc)[:120])

    def check(self) -> str:
        return "In-app messages are always on; phones get them as notifications once the person allows it."
