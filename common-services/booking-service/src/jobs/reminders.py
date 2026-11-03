# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reacts to scheduler ticks (job event-reminders): remind tomorrow's registrants once."""
from datetime import date, timedelta

from grepx_service import Emitter, Reader, now_iso, today_iso, state_of

from dto import EVENTS_TABLE, BOOKINGS_TABLE

JOB = "event-reminders"


def handle_tick(app, row, cfg, today: str | None = None) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    from routes.common import tell  # shared wording/values with the request routes

    class _Ctx:  # minimal adapter so tell() can use the emitter
        emitter = Emitter(app, cfg, cause=row)

    read, sent = Reader(app.client), 0
    tomorrow = (date.fromisoformat(today or today_iso()) + timedelta(days=1)).isoformat()
    for event in read.accepted(EVENTS_TABLE, event_date=tomorrow, state="open"):
        for reg in read.accepted(BOOKINGS_TABLE, event_id=event["_key"]):
            if reg.get("state") not in ("interested", "confirmed") or reg.get("reminded_at"):
                continue
            tell(_Ctx, "event_reminder", event, reg, ref=f"remind-{reg['_key']}")
            fields = state_of(reg)
            _Ctx.emitter.submit(BOOKINGS_TABLE, reg["_key"], "ACCEPTED", {**fields, "reminded_at": now_iso()})
            sent += 1
    _Ctx.emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": sent})
    return sent
