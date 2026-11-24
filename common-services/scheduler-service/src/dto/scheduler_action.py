# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions scheduler-service accepts."""
from enum import Enum


class SchedulerAction(str, Enum):
    REGISTER = "REGISTER"          # create or change a schedule (same schedule_id = change)
    CANCEL = "CANCEL"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    RUN_NOW = "RUN_NOW"            # one tick now, outside the rule
    PREVIEW = "PREVIEW"            # a rule's next times and words, before saving it
    SCHEDULES = "SCHEDULES"        # an organisation's schedules (optionally one owner's)
    TICKS = "TICKS"                # one schedule's latest ticks and how each went
    HEALTH = "HEALTH"              # is the ticker alive
