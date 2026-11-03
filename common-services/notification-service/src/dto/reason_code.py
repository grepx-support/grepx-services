"""Why a notification is rejected outright."""
from enum import Enum


class ReasonCode(str, Enum):
    UNKNOWN_TEMPLATE = "UNKNOWN_TEMPLATE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CHECK_FAILED = "CHECK_FAILED"
    MISSING_RECIPIENT = "MISSING_RECIPIENT"
