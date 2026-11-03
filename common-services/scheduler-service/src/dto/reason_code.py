"""Why a schedule request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_SCHEDULE = "INVALID_SCHEDULE"
