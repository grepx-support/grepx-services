"""Actions event-service accepts."""
from enum import Enum


class EventAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    CLONE = "CLONE"
    SET_IMAGES = "SET_IMAGES"
    COMPLETE = "COMPLETE"
    REOPEN = "REOPEN"
