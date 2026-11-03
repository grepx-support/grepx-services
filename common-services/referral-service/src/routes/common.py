# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Recompute one referrer's score from the people they invited and how many converted (projection, idempotent).

Where people live, what "converted" means and the points are deployment settings (the product deployment file):
    people.table, referral.join_points, referral.convert_points, referral.conversion.{table, field}
"""
from typing import Any

from grepx_service import Emitter, Reader
from grepx_service.plugins import person_table

from dto import SCORES_TABLE


def settings(cfg: Any) -> dict:
    r = cfg.get("referral") or {}
    conv = r.get("conversion") or {}
    return {"people": person_table(cfg), "join": int(r.get("join_points", 1)),
            "convert": int(r.get("convert_points", 2)), "conv_table": str(conv.get("table") or ""), "conv_field": str(conv.get("field") or "count")}


def converted(read: Reader, s: dict, person_id: str) -> bool:
    if not s["conv_table"]:
        return False
    return float((read.accepted_one(s["conv_table"], person_id) or {}).get(s["conv_field"]) or 0) > 0


def rescore(emitter: Emitter, read: Reader, referrer_id: str) -> dict:
    s = settings(emitter.cfg)
    friends = read.accepted(s["people"], referred_by=referrer_id)
    conv = sum(1 for f in friends if converted(read, s, f["_key"]))
    referrer = read.accepted_one(s["people"], referrer_id) or {}
    score = {"person_id": referrer_id, "name": referrer.get("name", ""), "joined": len(friends), "converted": conv,
             "points": s["join"] * len(friends) + s["convert"] * conv}
    emitter.submit(SCORES_TABLE, referrer_id, "ACCEPTED", score)
    return score
