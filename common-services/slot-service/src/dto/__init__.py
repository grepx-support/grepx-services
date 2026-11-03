"""Single import door for slot-service vocabulary."""
import grepx_contracts as gc
from .reason_code import ReasonCode
from .slot_action import SlotAction
from .slot_field import SlotField

SLOTS_TABLE = "slots"
BOOKINGS_TABLE = gc.booking.BOOKINGS
NOT_HOLDING = ("no_show", "not_eligible", "cancelled")

__all__ = ["ReasonCode", "SlotAction", "SlotField", "SLOTS_TABLE", "BOOKINGS_TABLE", "NOT_HOLDING"]
