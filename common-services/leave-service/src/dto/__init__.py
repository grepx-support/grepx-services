# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for leave-service vocabulary."""
from enum import Enum

import grepx_contracts as gc

LEAVES, TYPES = "leaves", "leave_types"
EMPLOYEES = gc.employee.EMPLOYEES       # employee-service's table (read only): who works where, start date


class LeaveAction(str, Enum):
    SAVE_TYPE = "SAVE_TYPE"      # a leave type: days a year, paid or not, carry-over
    REQUEST = "REQUEST"          # someone asks for leave (pending)
    DECIDE = "DECIDE"            # a manager approves or declines
    CANCEL = "CANCEL"            # taken back (pending or approved, not yet started)
    BALANCES = "BALANCES"        # allowance, taken, pending and left per type, per person, for a year
    CALENDAR = "CALENDAR"        # who is away between two dates (a site's people or everyone)


class LeaveState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_EMPLOYEE = "UNKNOWN_EMPLOYEE"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    UNKNOWN_LEAVE = "UNKNOWN_LEAVE"
    INVALID_DATE = "INVALID_DATE"
    INVALID_DAYS = "INVALID_DAYS"
    INVALID_NAME = "INVALID_NAME"
    OVERLAPS = "OVERLAPS"
    NOT_ENOUGH_BALANCE = "NOT_ENOUGH_BALANCE"
    ALREADY_DECIDED = "ALREADY_DECIDED"
    ALREADY_STARTED = "ALREADY_STARTED"


__all__ = ["LeaveAction", "LeaveState", "ReasonCode", "LEAVES", "TYPES", "EMPLOYEES"]
