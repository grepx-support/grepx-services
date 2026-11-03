"""Why an access request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_ROLE = "UNKNOWN_ROLE"
    SELF_DEMOTION = "SELF_DEMOTION"
    LAST_ADMIN = "LAST_ADMIN"
    UNKNOWN_STAFF_ROLE = "UNKNOWN_STAFF_ROLE"
    UNKNOWN_PERMISSION = "UNKNOWN_PERMISSION"
