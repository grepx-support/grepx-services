# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Image processing: EXIF-rotate, then the profile of what the image is for (Strategy). Pure (bytes in, bytes out).
picture: longest side 1920, WebP · avatar: 512 square, WebP · logo: longest side 800, transparency kept, PNG (documents
print PNG, and a logo on a coloured letterhead must keep its see-through background)."""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 15 * 1024 * 1024
FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "MPO"}
PICTURE_MAX_SIDE = 1920
AVATAR_SIDE = 512
LOGO_MAX_SIDE = 800


class ImageError(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    mode: str                 # RGB, or RGBA to keep transparency
    fmt: str                  # WEBP / PNG
    mime: str
    ext: str
    side: int
    square: bool = False

    def shape(self, img: Image.Image) -> Image.Image:
        if self.square:
            return ImageOps.fit(img, (self.side, self.side))
        img.thumbnail((self.side, self.side))
        return img

    def encode(self, img: Image.Image) -> bytes:
        out = io.BytesIO()
        img.save(out, self.fmt, **({"quality": 82} if self.fmt == "WEBP" else {"optimize": True}))
        return out.getvalue()


PROFILES = {"picture": Profile("RGB", "WEBP", "image/webp", "webp", PICTURE_MAX_SIDE),
            "avatar": Profile("RGB", "WEBP", "image/webp", "webp", AVATAR_SIDE, square=True),
            "logo": Profile("RGBA", "PNG", "image/png", "png", LOGO_MAX_SIDE)}


def open_image(data: bytes, mode: str) -> Image.Image:
    if len(data) > MAX_BYTES:
        raise ImageError("TOO_LARGE")
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in FORMATS:
            raise ImageError("NOT_AN_IMAGE")
        return ImageOps.exif_transpose(img).convert(mode)
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageError("NOT_AN_IMAGE") from exc


def process(data: bytes, kind: str) -> tuple[bytes, int, int]:
    profile = PROFILES[kind]
    img = profile.shape(open_image(data, profile.mode))
    return profile.encode(img), img.width, img.height
