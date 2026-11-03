# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reactions: a referred person joins (notify the referrer + rescore); a referred person converts (rescore)."""

from grepx_config.deployment import link
from grepx_service import Emitter, Reader, notify
from grepx_service.plugins import template_for

from routes.common import rescore, settings


def handle_person(app, row, cfg) -> str:
    referrer_id = row.fields.get("referred_by")
    if row.fields.get("status") != "ACCEPTED" or not referrer_id:
        return "ignored"
    emitter, read = Emitter(app, cfg, cause=row), Reader(app.client)
    rescore(emitter, read, referrer_id)
    referrer = read.accepted_one(settings(cfg)["people"], referrer_id) or {}
    notify(emitter, template_for(cfg, "referral_joined"), email=referrer.get("email", ""), phone=referrer.get("phone", ""),
           ref=f"joined-{row.key}", values={"first_name": referrer.get("name", "").split(" ")[0],
                                            "friend": row.fields.get("name", "").split(" ")[0], "link": link(cfg, "dashboard")},
           user_id=referrer_id)
    return "scored"


def handle_conversion(app, row, cfg) -> str:
    read = Reader(app.client)
    person = read.accepted_one(settings(cfg)["people"], row.key) or {}
    if row.fields.get("status") != "ACCEPTED" or not person.get("referred_by"):
        return "ignored"
    rescore(Emitter(app, cfg, cause=row), read, person["referred_by"])
    return "scored"
