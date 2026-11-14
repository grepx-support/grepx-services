# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""media-service: processing profiles, rejection of non-images, delete."""
import io
from pathlib import Path

import pytest
from grepx_testkit.harness import ServiceHarness
from grepx_storage import LocalStorage
from grepx_config import load_config
from PIL import Image

from routes import handle
from routes.common import Deps

cfg = load_config(Path(__file__).resolve().parents[1] / "config")


def png(w=3000, h=1000) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (w, h), "red").save(out, "PNG")
    return out.getvalue()


@pytest.fixture()
def h(tmp_path):
    Deps.storage = LocalStorage(tmp_path)
    return ServiceHarness().add(cfg, "media_requests", handle, cfg.live_criteria)


def process(h, data, kind):
    Deps.storage.put("staging/x", data)
    return h.call("media_requests", "media-service", {"action": "PROCESS", "staged_key": "staging/x", "kind": kind})


def test_picture_should_shrink_to_1920(h):
    v = process(h, png(), "picture")
    assert v.ok and (v.fields["width"], v.fields["height"]) == (1920, 640)
    assert Deps.storage.get(v.fields["key"])[:4] == b"RIFF" and Deps.storage.get("staging/x") is None


def test_avatar_should_be_square(h):
    v = process(h, png(), "avatar")
    assert (v.fields["width"], v.fields["height"]) == (512, 512)


def test_non_image_should_reject(h):
    assert process(h, b"not an image", "picture").reason == "NOT_AN_IMAGE"


def test_delete_should_remove_file(h):
    v = process(h, png(10, 10), "picture")
    assert h.call("media_requests", "media-service", {"action": "DELETE", "media_id": v.fields["media_id"]}).ok
    assert Deps.storage.get(v.fields["key"]) is None


def test_logo_keeps_transparency_as_png(h):
    out = io.BytesIO()
    Image.new("RGBA", (1600, 400), (255, 0, 0, 0)).save(out, "PNG")
    v = process(h, out.getvalue(), "logo")
    assert v.ok and (v.fields["width"], v.fields["height"]) == (800, 200) and v.fields["content_type"] == "image/png"
    stored = Image.open(io.BytesIO(Deps.storage.get(v.fields["key"])))
    assert stored.format == "PNG" and stored.mode == "RGBA" and stored.getpixel((0, 0))[3] == 0
