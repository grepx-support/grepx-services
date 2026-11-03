# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Booking rules. Pure.

A person has one booking per event. Re-registering never downgrades:
interested < confirmed < no_show = not_eligible < attended. attended/no_show may only be set on the event day;
staff may mark someone not eligible any day (re-registering does not undo it).
"""
import hashlib

RANK = {"cancelled": -1, "interested": 0, "confirmed": 1, "no_show": 2, "not_eligible": 2, "attended": 3}
DAY_ONLY = ("attended", "no_show")


def merge_state(current: str | None, wanted: str) -> str:
    if current in (None, "", "cancelled"):
        return wanted
    return wanted if RANK.get(wanted, 0) > RANK.get(current, 0) else current


def booking_key(event_id: str, person_id: str = "", email: str = "", phone: str = "") -> str:
    who = person_id or "g-" + hashlib.sha1(f"{email.lower()}|{phone}".encode()).hexdigest()[:12]
    return f"{event_id}-{who}"
