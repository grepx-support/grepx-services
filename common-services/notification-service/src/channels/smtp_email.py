# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Email over SMTP (587 STARTTLS or 465 SSL), with files attached when the message has them (a PDF order, an invoice)."""
import os
import smtplib
from email.message import EmailMessage

from .base import Channel


class SmtpEmailChannel(Channel):
    name = "email"

    def __init__(self, env=os.environ):
        self.host, self.port = env.get("SMTP_HOST", ""), int(env.get("SMTP_PORT", "587") or 587)
        self.user, self.password = env.get("SMTP_USER", ""), env.get("SMTP_PASS", "") or env.get("SMTP_PASSWORD", "")  # SMTP_PASS: the name the Integrations page and the original .env use
        self.sender = env.get("SMTP_FROM", "") or self.user

    def configured(self) -> bool:
        return bool(self.host and self.sender)

    def _connect(self):
        smtp = (smtplib.SMTP_SSL if self.port == 465 else smtplib.SMTP)(self.host, self.port, timeout=20)
        if self.port != 465:
            smtp.starttls()
        if self.user:
            smtp.login(self.user, self.password)
        return smtp

    def check(self) -> str:
        with self._connect():
            return f"Signed in to {self.host} as {self.user or self.sender}"

    def build(self, recipient, subject, body, html=None, attachments=None) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = subject, self.sender, recipient
        msg.set_content(body)
        if html:
            msg.add_alternative(html, subtype="html")
        for a in attachments or []:
            main, _, sub = (a.get("mime") or "application/octet-stream").partition("/")
            msg.add_attachment(a["data"], maintype=main, subtype=sub or "octet-stream", filename=a.get("name") or "file")
        return msg

    def send(self, recipient, subject, body, html=None, attachments=None) -> None:
        msg = self.build(recipient, subject, body, html, attachments)
        with self._connect() as smtp:
            smtp.send_message(msg)
