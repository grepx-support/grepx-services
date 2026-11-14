# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""multipart/form-data body for a file upload with plain urllib (no extra library)."""
from __future__ import annotations

import secrets


def encode(fields: dict[str, str], file_field: str, name: str, mime: str, data: bytes) -> tuple[bytes, str]:
    """(body, content type header)."""
    boundary = "grepx" + secrets.token_hex(12)
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    head = f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'
    body = b"".join(parts) + head.encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"
