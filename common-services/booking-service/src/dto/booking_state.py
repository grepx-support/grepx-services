# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Where a person stands for one event."""
from enum import Enum


class BookingState(str, Enum):
    INTERESTED = "interested"
    CONFIRMED = "confirmed"
    NO_SHOW = "no_show"
    NOT_ELIGIBLE = "not_eligible"   # screened out (staff decision, any day); frees the slot
    ATTENDED = "attended"
    CANCELLED = "cancelled"
