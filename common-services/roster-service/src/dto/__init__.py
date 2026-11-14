# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for roster-service vocabulary."""
from enum import Enum

import grepx_contracts as gc

SHIFTS, ATTENDANCE, PINS = "shifts", "attendance", "clock_pins"
EMPLOYEES = gc.employee.EMPLOYEES  # employee-service's table (read only): pay basis for the cost of a week


class RosterAction(str, Enum):
    SAVE_SHIFT = "SAVE_SHIFT"      # add or change one shift (draft until the week is published)
    REMOVE_SHIFT = "REMOVE_SHIFT"
    COPY_WEEK = "COPY_WEEK"        # last week's shifts at a site into another week (skips clashes)
    PUBLISH_WEEK = "PUBLISH_WEEK"  # staff see their shifts
    WEEK = "WEEK"                  # a site's week: shifts, hours and cost per person, warnings
    SET_PIN = "SET_PIN"            # the person's clock PIN (only its hash is kept)
    CLOCK = "CLOCK"                # clock in, or out when already in (PIN or the person's own login)


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_EMPLOYEE = "UNKNOWN_EMPLOYEE"
    UNKNOWN_SHIFT = "UNKNOWN_SHIFT"
    INVALID_TIME = "INVALID_TIME"
    INVALID_DATE = "INVALID_DATE"
    MISSING_SITE = "MISSING_SITE"
    DOUBLE_BOOKED = "DOUBLE_BOOKED"
    WRONG_PIN = "WRONG_PIN"
    INVALID_PIN = "INVALID_PIN"
    NOT_AT_THIS_SITE = "NOT_AT_THIS_SITE"


__all__ = ["RosterAction", "ReasonCode", "SHIFTS", "ATTENDANCE", "PINS", "EMPLOYEES"]
