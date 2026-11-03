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
    SLOT = "slot"
