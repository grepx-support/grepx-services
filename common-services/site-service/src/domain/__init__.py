# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a business's public page may hold (no I/O): text limits, a colour, links that are web addresses, social
profiles, promotions with an optional end date, video links turned into YouTube video ids, sections on / off.
What visitors see: the page without promotions that have ended (public_view)."""
from __future__ import annotations

import re
from datetime import date

from dto import Section

SECTIONS = tuple(s.value for s in Section)     # offers, highlights, brands, videos, social, visit, sign_in

TEXT = {"company": 80, "tagline": 140, "headline": 160, "intro": 600, "phone": 30, "whatsapp": 30, "email": 120, "address": 300,
        "hours": 160, "logo_id": 64, "cover_id": 64, "footer": 200}
SOCIAL = ("instagram", "facebook", "youtube", "website", "map")
MAX_PROMOTIONS, MAX_HIGHLIGHTS, MAX_BRANDS, MAX_VIDEOS = 12, 8, 24, 6
COLOR = re.compile(r"#[0-9a-fA-F]{6}")
LINK = re.compile(r"https?://[^\s/$.?#][^\s]{1,400}", re.IGNORECASE)
YOUTUBE = re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})")


def _text(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit] if limit < 300 else str(value or "").strip()[:limit]


def _link(value) -> str:
    """'' or an http(s) address; a bare 'instagram.com/x' gets https:// in front. Raises INVALID_LINK otherwise."""
    v = str(value or "").strip()
    if not v:
        return ""
    if not re.match(r"https?://", v, re.IGNORECASE):
        v = f"https://{v}"
    if not LINK.fullmatch(v):
        raise ValueError("INVALID_LINK")
    return v


def _day(value) -> str:
    v = str(value or "").strip()[:10]
    if not v:
        return ""
    try:
        return date.fromisoformat(v).isoformat()
    except ValueError:
        raise ValueError("INVALID_DATE")


def video_id(value) -> str:
    """The 11-character YouTube id in a watch, youtu.be, shorts, embed or live link (or the id itself); '' if none."""
    v = str(value or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", v):
        return v
    m = YOUTUBE.search(v)
    return m.group(1) if m else ""


def clean_page(raw: dict) -> dict:
    """The page as stored. Raises ValueError(reason): INVALID_PAGE (no name), INVALID_COLOR, INVALID_LINK, INVALID_DATE."""
    if not isinstance(raw, dict):
        raise ValueError("INVALID_PAGE")
    out = {k: _text(raw.get(k), n) for k, n in TEXT.items()}
    if not out["company"]:
        raise ValueError("INVALID_PAGE")
    color = str(raw.get("color") or "#C9A96E")
    if not COLOR.fullmatch(color):
        raise ValueError("INVALID_COLOR")
    social = {k: _link((raw.get("social") or {}).get(k)) for k in SOCIAL}
    promotions = []
    for p in (raw.get("promotions") or [])[:MAX_PROMOTIONS]:
        if not isinstance(p, dict) or not str(p.get("title") or "").strip():
            continue
        promotions.append({"title": _text(p.get("title"), 90), "text": _text(p.get("text"), 240), "badge": _text(p.get("badge"), 24),
                           "starts": _day(p.get("starts")), "ends": _day(p.get("ends")), "link": _link(p.get("link")),
                           "image_id": _text(p.get("image_id"), 64)})
    highlights = [{"title": _text(h.get("title"), 60), "text": _text(h.get("text"), 200)}
                  for h in (raw.get("highlights") or []) if isinstance(h, dict) and str(h.get("title") or "").strip()][:MAX_HIGHLIGHTS]
    brands = [_text(b, 30) for b in (raw.get("brands") or []) if str(b).strip()][:MAX_BRANDS]
    videos = []
    for v in raw.get("videos") or []:
        vid = video_id(v)
        if vid and vid not in videos:
            videos.append(vid)
    sections = raw.get("sections") or {}
    return {**out, "color": color, "social": social, "promotions": promotions, "highlights": highlights, "brands": brands,
            "videos": videos[:MAX_VIDEOS], "sections": {s: bool(sections.get(s, True)) for s in SECTIONS}}


def public_view(page: dict, today: date | None = None) -> dict:
    """What visitors see: promotions that have not started or have ended are left out, switched-off sections emptied."""
    today = (today or date.today()).isoformat()
    on = page.get("sections") or {}
    live = [p for p in page.get("promotions") or [] if (not p.get("starts") or p["starts"] <= today) and (not p.get("ends") or p["ends"] >= today)]
    return {**page, "promotions": live if on.get("offers", True) else [], "highlights": page.get("highlights") if on.get("highlights", True) else [],
            "brands": page.get("brands") if on.get("brands", True) else [], "videos": page.get("videos") if on.get("videos", True) else []}
