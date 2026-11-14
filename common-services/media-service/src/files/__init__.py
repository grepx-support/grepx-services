# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Files kept as they are (attachments): what a file is from its first bytes, and a safe name. Pure."""
from __future__ import annotations

import re

MAX_BYTES = 10 * 1024 * 1024

MAGIC = [(b"%PDF-", "application/pdf", "pdf"), (b"\x89PNG", "image/png", "png"), (b"\xff\xd8\xff", "image/jpeg", "jpg"),
         (b"GIF8", "image/gif", "gif")]
OFFICE = {"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
TEXT = {"csv": "text/csv", "txt": "text/plain"}


def safe_name(name: str) -> str:
    base = re.sub(r"[^\w .()\-]", "_", str(name or "file").replace("\\", "/").split("/")[-1]).strip(" .")
    return (base or "file")[:120]


def kind_of(data: bytes, name: str) -> tuple[str, str]:
    """(content type, extension). Only documents and pictures: PDF, PNG, JPEG, GIF, WebP, Word / Excel / PowerPoint, CSV,
    plain text. Refuses NOT_ALLOWED (anything else - programs, archives, HTML), TOO_LARGE, MISSING_FILE."""
    if not data:
        raise ValueError("MISSING_FILE")
    if len(data) > MAX_BYTES:
        raise ValueError("TOO_LARGE")
    for magic, mime, ext in MAGIC:
        if data.startswith(magic):
            return mime, ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    ext = safe_name(name).rsplit(".", 1)[-1].lower() if "." in str(name) else ""
    if data.startswith(b"PK\x03\x04") and ext in OFFICE:
        return OFFICE[ext], ext
    if ext in TEXT:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("NOT_ALLOWED")
        if "<script" not in text.lower():
            return TEXT[ext], ext
    raise ValueError("NOT_ALLOWED")
