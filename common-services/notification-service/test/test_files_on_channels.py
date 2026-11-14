# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Files on WhatsApp: Twilio gets the file's public link, Meta gets the file uploaded and sent as a document."""
import base64

from channels.meta_whatsapp import MetaWhatsAppChannel
from channels.multipart import encode
from channels.twilio import TwilioSmsChannel, TwilioWhatsAppChannel
from routes.send import attachments

PDF = {"name": "PO-12.pdf", "mime": "application/pdf", "data": b"%PDF-1", "url": "https://k.example/api/v1/files/t/PO-12.pdf"}
ENV = {"TWILIO_SID": "AC1", "TWILIO_TOKEN": "t", "TWILIO_WHATSAPP_FROM": "+15550001", "TWILIO_SMS_FROM": "+15550002"}


def test_twilio_whatsapp_sends_the_link_sms_does_not():
    wa = TwilioWhatsAppChannel(ENV).form("+6591234567", "Order 12", [PDF, {**PDF, "url": ""}])
    assert ("MediaUrl", PDF["url"]) in wa and sum(1 for k, _ in wa if k == "MediaUrl") == 1
    assert not [k for k, _ in TwilioSmsChannel(ENV).form("+6591234567", "Order 12", [PDF]) if k == "MediaUrl"]


def test_meta_uploads_then_sends_the_document():
    calls = []
    ch = MetaWhatsAppChannel({"WHATSAPP_TOKEN": "x", "WHATSAPP_PHONE_ID": "99"})
    ch._post = lambda path, data, ctype: calls.append((path, ctype, data)) or ({"id": "m1"} if path.endswith("/media") else {})
    ch.send("+65 9123 4567", "Order", "Please supply", attachments=[PDF])
    assert [c[0] for c in calls] == ["99/messages", "99/media", "99/messages"]
    assert calls[1][1].startswith("multipart/form-data") and b"%PDF-1" in calls[1][2]
    assert b'"document": {"id": "m1", "filename": "PO-12.pdf"}' in calls[2][2] and b'"to": "6591234567"' in calls[2][2]


def test_multipart_and_attachment_decoding():
    body, ctype = encode({"a": "1"}, "file", "x.pdf", "application/pdf", b"DATA")
    assert ctype.split("boundary=")[1].encode() in body and b'name="file"; filename="x.pdf"' in body
    files = attachments([{"name": "x.pdf", "data_b64": "REFUQQ==", "url": "https://u"}])
    assert files == [{"name": "x.pdf", "mime": "application/octet-stream", "data": b"DATA", "url": "https://u"}]
    big = base64.b64encode(b"x" * (5 * 1024 * 1024)).decode()
    assert attachments([{"data_b64": big}, {"data_b64": big}]) is None                          # over 8 MB together
