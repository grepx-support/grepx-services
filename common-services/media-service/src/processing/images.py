# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Image processing: EXIF-rotate, RGB, resize by profile, WebP q82. Pure (bytes in, bytes out)."""
from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 15 * 1024 * 1024
FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "MPO"}
PICTURE_MAX_SIDE = 1920
AVATAR_SIDE = 512


class ImageError(ValueError):
    pass


def process(data: bytes, kind: str) -> tuple[bytes, int, int]:
    if len(data) > MAX_BYTES:
        raise ImageError("TOO_LARGE")
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in FORMATS:
            raise ImageError("NOT_AN_IMAGE")
        img = ImageOps.exif_transpose(img).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageError("NOT_AN_IMAGE") from exc
    if kind == "avatar":
        img = ImageOps.fit(img, (AVATAR_SIDE, AVATAR_SIDE))
    else:
        img.thumbnail((PICTURE_MAX_SIDE, PICTURE_MAX_SIDE))
    out = io.BytesIO()
    img.save(out, "WEBP", quality=82)
    return out.getvalue(), img.width, img.height
