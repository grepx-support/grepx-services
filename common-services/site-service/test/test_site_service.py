# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""site-service: a business's public page is cleaned and kept; visitors don't see ended promotions or switched-off parts."""
from datetime import date
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_page, public_view, video_id
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
PAGE = {"company": " Galaxy  Mobiles ", "headline": "Newest phones, best price", "color": "#123abc",
        "social": {"instagram": "instagram.com/galaxy", "youtube": "https://www.youtube.com/@galaxy"},
        "promotions": [{"title": "Exchange bonus", "badge": "LIVE", "ends": "2026-12-31", "link": "galaxy.in/offers"},
                       {"title": "Old one", "ends": "2026-01-01"}, {"title": ""}, {"title": "Soon", "starts": "2027-01-05"}],
        "videos": ["https://youtu.be/dQw4w9WgXcQ", "https://www.youtube.com/shorts/aBcDeFgHiJk", "not a video", "dQw4w9WgXcQ"],
        "highlights": [{"title": "IMEI-verified", "text": "Every unit"}], "brands": ["A", " ", "B"], "sections": {"brands": False}}


def test_clean_page_and_what_visitors_see():
    page = clean_page(PAGE)
    assert page["company"] == "Galaxy Mobiles" and page["social"]["instagram"] == "https://instagram.com/galaxy"
    assert [p["title"] for p in page["promotions"]] == ["Exchange bonus", "Old one", "Soon"]
    assert page["promotions"][0]["link"] == "https://galaxy.in/offers"
    assert page["videos"] == ["dQw4w9WgXcQ", "aBcDeFgHiJk"] and page["brands"] == ["A", "B"]
    assert page["sections"]["brands"] is False and page["sections"]["offers"] is True
    seen = public_view(page, date(2026, 11, 16))
    assert [p["title"] for p in seen["promotions"]] == ["Exchange bonus"] and seen["brands"] == []
    assert video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10") == "dQw4w9WgXcQ" and video_id("x") == ""
    for bad, reason in (({"company": ""}, "INVALID_PAGE"), ({"color": "red"}, "INVALID_COLOR"),
                        ({"social": {"facebook": "not a link"}}, "INVALID_LINK"), ({"promotions": [{"title": "x", "ends": "31/12"}]}, "INVALID_DATE")):
        with pytest.raises(ValueError, match=reason):
            clean_page({**PAGE, **bad})


def test_save_keeps_one_page_per_business():
    h = ServiceHarness().add(cfg, "site_requests", handle, cfg.live_criteria)
    assert h.call("site_requests", "site-service", {"action": "SAVE", "page": PAGE}).reason == "MISSING_BUSINESS"
    assert h.call("site_requests", "site-service", {"action": "SAVE", "business_id": "b1", "page": {**PAGE, "color": "x"}}).reason == "INVALID_COLOR"
    assert h.call("site_requests", "site-service", {"action": "SAVE", "business_id": "b1", "page": PAGE, "actor_id": "u1"}).ok
    assert h.call("site_requests", "site-service", {"action": "SAVE", "business_id": "b1", "page": {**PAGE, "headline": "New"}}).ok
    rows = h.rows("business_pages")
    assert len(rows) == 1 and rows[0]["headline"] == "New" and rows[0]["business_id"] == "b1"
