"""Actions scheduler-service accepts."""
from enum import Enum


class SchedulerAction(str, Enum):
    REGISTER = "REGISTER"
    CANCEL = "CANCEL"
