# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SMS and WhatsApp through Twilio's REST API (Template Method: only the address format differs).
Twilio fetches files itself, so a file goes as its public link (MediaUrl) - attachments without a link are left out."""
import base64
import json
import os
import urllib.parse
import urllib.request

from .base import Channel


class TwilioChannel(Channel):
    prefix = ""
    from_env = ""

    def __init__(self, env=os.environ):
        self.sid, self.token = env.get("TWILIO_SID", ""), env.get("TWILIO_TOKEN", "")
        self.sender = env.get(self.from_env, "")

    def configured(self) -> bool:
        return bool(self.sid and self.token and self.sender)

    def address(self, number: str) -> str:
        return f"{self.prefix}{number}"

    def _call(self, path: str, data: bytes | None = None) -> dict:
        req = urllib.request.Request(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}{path}", data=data)
        req.add_header("Authorization", "Basic " + base64.b64encode(f"{self.sid}:{self.token}".encode()).decode())
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read() or b"{}")

    def check(self) -> str:
        return f"Connected to Twilio account “{self._call('.json').get('friendly_name', self.sid)}”"

    def form(self, recipient: str, body: str, attachments=None) -> list[tuple[str, str]]:
        media = [("MediaUrl", a["url"]) for a in attachments or [] if a.get("url")][:10] if self.carries_files else []
        return [("From", self.address(self.sender)), ("To", self.address(recipient)), ("Body", body), *media]

    carries_files = False

    def send(self, recipient, subject, body, html=None, attachments=None) -> None:
        self._call("/Messages.json", urllib.parse.urlencode(self.form(recipient, body, attachments)).encode())


class TwilioSmsChannel(TwilioChannel):
    name, from_env = "sms", "TWILIO_SMS_FROM"


class TwilioWhatsAppChannel(TwilioChannel):
    name, prefix, from_env = "whatsapp", "whatsapp:", "TWILIO_WHATSAPP_FROM"
    carries_files = True
