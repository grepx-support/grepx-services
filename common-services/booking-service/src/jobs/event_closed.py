# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reacts to an event being completed: everyone still interested/confirmed becomes a no-show (idempotent)."""
from grepx_service import Emitter, Reader, now_iso, state_of

from dto import BOOKINGS_TABLE

OPEN = ("interested", "confirmed")


def handle_event(app, row, cfg) -> int:
    if row.fields.get("state") != "completed" or row.fields.get("status") != "ACCEPTED":
        return 0
    emitter, closed = Emitter(app, cfg, cause=row), 0
    for reg in Reader(app.client).accepted(BOOKINGS_TABLE, event_id=row.key):
        if reg.get("state") in OPEN:
            fields = state_of(reg)
            emitter.submit(BOOKINGS_TABLE, reg["_key"], "ACCEPTED", {**fields, "state": "no_show", "updated": now_iso()})
            closed += 1
    return closed
