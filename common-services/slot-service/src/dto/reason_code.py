# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a slot request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    INVALID_PLAN = "INVALID_PLAN"
    HAS_BOOKINGS = "HAS_BOOKINGS"
    UNKNOWN_SLOT = "UNKNOWN_SLOT"
    BELOW_BOOKED = "BELOW_BOOKED"
    TOO_HIGH = "TOO_HIGH"
