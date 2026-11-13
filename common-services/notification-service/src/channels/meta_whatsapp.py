# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""WhatsApp through Meta's WhatsApp Cloud API (a business number on Meta, no Twilio in between).
Free text reaches people who wrote to the business in the last 24 hours; outside that window Meta asks for an
approved template - the provider's refusal is recorded as the delivery error."""
import json
import os
import re
import urllib.request

from .base import Channel

GRAPH = "https://graph.facebook.com/v20.0"


class MetaWhatsAppChannel(Channel):
    name = "whatsapp"

    def __init__(self, env=os.environ):
        self.token, self.phone_id = env.get("WHATSAPP_TOKEN", ""), env.get("WHATSAPP_PHONE_ID", "")

    def configured(self) -> bool:
        return bool(self.token and self.phone_id)

    def _call(self, path: str, payload: dict | None = None) -> dict:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=json.dumps(payload).encode() if payload else None,
                                     headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read() or b"{}")

    @staticmethod
    def payload(recipient: str, body: str) -> dict:
        """The message Meta expects: international number without "+" or spaces, plain text."""
        return {"messaging_product": "whatsapp", "to": re.sub(r"\D", "", recipient), "type": "text", "text": {"body": body[:4096]}}

    def check(self) -> str:
        info = self._call(f"{self.phone_id}?fields=display_phone_number,verified_name")
        return f"Connected to WhatsApp number {info.get('display_phone_number', self.phone_id)} ({info.get('verified_name', 'Meta')})"

    def send(self, recipient, subject, body, html=None, attachments=None) -> None:
        self._call(f"{self.phone_id}/messages", self.payload(recipient, f"{subject}\n\n{body}" if subject else body))
