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
