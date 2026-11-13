# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The scheduler's tick (job notify-retry): send failed messages again once their wait is over (domain/retry.py)."""
from datetime import datetime, timezone

from grepx_service import Emitter, Reader, now_iso

from domain import retry

JOB = "notify-retry"
TABLE = "notifications"
SERVICE = "notification-service"


def handle_tick(app, row, cfg, now: datetime | None = None) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    read, emitter = Reader(app.client), Emitter(app, cfg, cause=row)
    due = retry.due(read.accepted(TABLE, delivery="FAILED"), now or datetime.now(timezone.utc),
                    tried=lambda key: read.one(TABLE, key) is not None)
    for failed in due:
        emitter.request(TABLE, retry.next_key(failed), retry.again(failed), SERVICE)
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": len(due)})
    return len(due)
