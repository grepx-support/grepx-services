# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A business's pipeline: its stages in order - each with a win chance (for the weighted forecast), a colour and how
many days without activity before a deal there counts as stale. Pure."""
from __future__ import annotations

import re

DEFAULT = [
    {"stage_id": "new", "name": "New enquiry", "chance": 10, "color": "#64748b", "stale_days": 3},
    {"stage_id": "qualified", "name": "Qualified", "chance": 25, "color": "#0ea5e9", "stale_days": 5},
    {"stage_id": "quote", "name": "Quote sent", "chance": 50, "color": "#8b5cf6", "stale_days": 7},
    {"stage_id": "negotiation", "name": "Negotiation", "chance": 75, "color": "#f59e0b", "stale_days": 5},
]
MAX_STAGES = 12


def stages_of(row: dict | None) -> list[dict]:
    return (row or {}).get("stages") or DEFAULT


def clean_stages(raw) -> list[dict]:
    """Checked stages in the order given. Refuses INVALID_STAGES: none, too many, a blank name, the same id twice."""
    if not raw or len(raw) > MAX_STAGES:
        raise ValueError("INVALID_STAGES")
    out, seen = [], set()
    for n, s in enumerate(raw):
        name = " ".join(str(s.get("name") or "").split())[:40]
        sid = str(s.get("stage_id") or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"s{n}")[:40]
        if not name or sid in seen:
            raise ValueError("INVALID_STAGES")
        seen.add(sid)
        color = str(s.get("color") or "#64748b")
        out.append({"stage_id": sid, "name": name, "chance": max(0, min(100, int(s.get("chance") or 0))),
                    "color": color if re.fullmatch(r"#[0-9a-fA-F]{6}", color) else "#64748b", "stale_days": max(1, int(s.get("stale_days") or 7))})
    return out
