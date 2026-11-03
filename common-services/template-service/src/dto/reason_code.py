"""Why a template request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_TEMPLATE = "UNKNOWN_TEMPLATE"
    UNKNOWN_PLACEHOLDER = "UNKNOWN_PLACEHOLDER"
    UNKNOWN_CHANNEL = "UNKNOWN_CHANNEL"
