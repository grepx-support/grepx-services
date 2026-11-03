"""How often a schedule fires."""
from enum import Enum


class ScheduleKind(str, Enum):
    EVERY_MINUTES = "EVERY_MINUTES"
    DAILY_AT = "DAILY_AT"
