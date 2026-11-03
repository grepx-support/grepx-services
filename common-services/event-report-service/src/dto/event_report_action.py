"""Actions event-report-service accepts."""
from enum import Enum


class EventReportAction(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    SAVE_RETRO = "SAVE_RETRO"
