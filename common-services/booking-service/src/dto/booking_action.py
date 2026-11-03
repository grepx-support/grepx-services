# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions booking-service accepts."""
from enum import Enum


class BookingAction(str, Enum):
    INTEREST = "INTEREST"
    BOOK = "BOOK"
    CANCEL = "CANCEL"
    MOVE = "MOVE"
    CHECK_IN = "CHECK_IN"
    MARK = "MARK"
