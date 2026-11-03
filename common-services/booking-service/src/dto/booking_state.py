"""Where a person stands for one event."""
from enum import Enum


class BookingState(str, Enum):
    INTERESTED = "interested"
    CONFIRMED = "confirmed"
    NO_SHOW = "no_show"
    NOT_ELIGIBLE = "not_eligible"   # screened out (staff decision, any day); frees the slot
    ATTENDED = "attended"
    CANCELLED = "cancelled"
