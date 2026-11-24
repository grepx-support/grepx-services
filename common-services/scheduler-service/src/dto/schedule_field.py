# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of schedules and ticks."""
from enum import Enum


class ScheduleField(str, Enum):
    SCHEDULE_ID = "schedule_id"
    JOB = "job"
    TARGET_SERVICE = "target_service"
    KIND = "kind"
    EVERY_MINUTES = "every_minutes"
    AT = "at"
    CRON = "cron"                  # CRON: the cron line
    TIMEZONE = "timezone"          # CRON / DAILY_AT: IANA name (UTC, Asia/Singapore)
    SLOT = "slot"
    TENANT_ID = "tenant_id"
    OWNER = "owner"                # who registered it, to list them together (e.g. sea:<sea_id>)
    LABEL = "label"                # what people call it ("Crypto · daily data")
    PAYLOAD = "payload"            # JSON handed to the target with every tick (which sea, which job)
    PAUSED = "paused"
    SINCE = "since"                # slots after this time fire (set when registered or resumed - no burst of old slots)
    LAST_FIRED = "last_fired"
    NEXT_RUNS = "next_runs"        # the next five times, comma-separated ISO
    WORDS = "words"                # the rule in words ("every day at 00:20 UTC")
    MANUAL = "manual"              # a tick from Run now
    LIMIT = "limit"
