# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for payroll-service vocabulary."""
from enum import Enum

import grepx_contracts as gc

SETTINGS, RUNS, SLIPS, ADJUSTMENTS = "payroll_settings", "pay_runs", "payslips", "pay_adjustments"
EMPLOYEES, ATTENDANCE, LEAVES = gc.employee.EMPLOYEES, gc.roster.ATTENDANCE, gc.leave.LEAVES     # read only


class PayrollAction(str, Enum):
    SETTINGS = "SETTINGS"          # the business's country and every rate (country defaults + its own changes), and the countries offered
    SET_SETTINGS = "SET_SETTINGS"  # change the country or any rate
    ADJUST = "ADJUST"              # a bonus, an advance to recover, or another deduction for one person and month
    REMOVE_ADJUSTMENT = "REMOVE_ADJUSTMENT"
    RUN = "RUN"                    # work out the month's payslips (again, while the run is a draft)
    FINALISE = "FINALISE"          # lock the month: payslips can be sent and no longer change
    MONTH = "MONTH"                # the month's run and payslips
    SEND_PAYSLIP = "SEND_PAYSLIP"  # send one locked payslip to the person (email / WhatsApp / SMS, the PDF attached)


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_COUNTRY = "UNKNOWN_COUNTRY"
    UNKNOWN_EMPLOYEE = "UNKNOWN_EMPLOYEE"
    UNKNOWN_SETTING = "UNKNOWN_SETTING"
    INVALID_MONTH = "INVALID_MONTH"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    ALREADY_FINAL = "ALREADY_FINAL"
    NO_RUN = "NO_RUN"
    MONTH_NOT_FINAL = "MONTH_NOT_FINAL"
    INVALID_CHANNEL = "INVALID_CHANNEL"
    NO_CONTACT = "NO_CONTACT"


__all__ = ["PayrollAction", "ReasonCode", "SETTINGS", "RUNS", "SLIPS", "ADJUSTMENTS", "EMPLOYEES", "ATTENDANCE", "LEAVES"]
