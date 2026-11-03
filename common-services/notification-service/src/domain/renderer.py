# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Render a message: admin custom wording wins, else the channel's built-in body, else the generic text body.

Placeholders are plain {name} substitution — never executable template code —
so admins can edit wording safely. Email gets paragraphs + linkified URLs in a
small branded layout; SMS/WhatsApp stay plain text.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Optional

_PLACEHOLDER = re.compile(r"\{(\w+)\}")
_URL = re.compile(r"(https?://[^\s<]+)")


@dataclass
class Message:
    subject: str
    body: str
    html: Optional[str] = None


def fill(text: str, values: dict) -> str:
    return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), m.group(0))), text or "")


def _html(text: str, org: str) -> str:
    def para(p: str) -> str:
        escaped = html.escape(p).replace("\n", "<br>")
        return "<p>" + _URL.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', escaped) + "</p>"

    paragraphs = "".join(para(p) for p in re.split(r"\n\s*\n", text.strip()) if p.strip())
    return (f"<div style=\"font-family:Arial,sans-serif;max-width:560px;margin:auto\"><h2 style=\"color:#e11d48\">{html.escape(org)}</h2>"
            f"{paragraphs}<p style=\"color:#888;font-size:12px\">{html.escape(org)}</p></div>")


def render(template: dict, settings: Optional[dict], channel: str, values: dict, org: str) -> Message:
    bodies = template.get("bodies") or {}
    custom = (settings or {}).get("text") or ""
    if custom.strip():
        subject, text = (settings or {}).get("subject") or "", custom
    else:
        subject, text = bodies.get("subject", ""), bodies.get(channel) or bodies.get("text", "")
    text = fill(text, values).strip()
    subject = fill(subject, values).strip() or (text.splitlines()[0][:80] if text else "")
    return Message(subject, text, _html(text, org) if channel == "email" else None)
