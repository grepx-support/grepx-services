"""Actions slot-service accepts."""
from enum import Enum


class SlotAction(str, Enum):
    GENERATE = "GENERATE"
    SET_CAPACITY = "SET_CAPACITY"
    SET_ALL = "SET_ALL"
