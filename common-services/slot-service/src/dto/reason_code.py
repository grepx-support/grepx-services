"""Why a slot request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    INVALID_PLAN = "INVALID_PLAN"
    HAS_BOOKINGS = "HAS_BOOKINGS"
    UNKNOWN_SLOT = "UNKNOWN_SLOT"
    BELOW_BOOKED = "BELOW_BOOKED"
    TOO_HIGH = "TOO_HIGH"
