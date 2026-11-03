"""Why a task request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_TASK = "UNKNOWN_TASK"
    NOT_ALLOWED = "NOT_ALLOWED"
    INVALID_STATE = "INVALID_STATE"
    ALREADY_ASSIGNED = "ALREADY_ASSIGNED"
