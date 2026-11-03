"""Why a checklist request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_TEMPLATE = "UNKNOWN_TEMPLATE"
