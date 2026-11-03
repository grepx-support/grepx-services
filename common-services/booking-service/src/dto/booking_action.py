"""Actions booking-service accepts."""
from enum import Enum


class BookingAction(str, Enum):
    INTEREST = "INTEREST"
    BOOK = "BOOK"
    CANCEL = "CANCEL"
    MOVE = "MOVE"
    CHECK_IN = "CHECK_IN"
    MARK = "MARK"
