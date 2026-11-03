"""Event lifecycle."""
from enum import Enum


class EventState(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
