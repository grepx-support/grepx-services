# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a booking request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_EVENT = "UNKNOWN_EVENT"
    EVENT_CLOSED = "EVENT_CLOSED"
    SLOT_REQUIRED = "SLOT_REQUIRED"
    UNKNOWN_SLOT = "UNKNOWN_SLOT"
    SLOT_FULL = "SLOT_FULL"
    NOT_REGISTERED = "NOT_REGISTERED"
    ALREADY_ATTENDED = "ALREADY_ATTENDED"
    NOT_EVENT_DAY = "NOT_EVENT_DAY"
    INVALID_STATE = "INVALID_STATE"
