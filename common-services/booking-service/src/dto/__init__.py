"""Single import door for booking-service vocabulary."""
import grepx_contracts as gc
from .reason_code import ReasonCode
from .booking_action import BookingAction
from .booking_field import BookingField
from .booking_state import BookingState

BOOKINGS_TABLE = "bookings"
EVENTS_TABLE = gc.event.EVENTS
SLOTS_TABLE = gc.slot.SLOTS
NOT_HOLDING = (BookingState.NO_SHOW.value, BookingState.NOT_ELIGIBLE.value, BookingState.CANCELLED.value)

__all__ = ["ReasonCode", "BookingAction", "BookingField", "BookingState", "BOOKINGS_TABLE", "EVENTS_TABLE",
           "SLOTS_TABLE", "NOT_HOLDING"]
