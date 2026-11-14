# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for compliance-service vocabulary."""
from enum import Enum

POINTS, LOGS = "check_points", "check_logs"


class ComplianceAction(str, Enum):
    SAVE_POINT = "SAVE_POINT"      # a check at a site: a reading with a safe range, or a yes / no checklist; how often
    REMOVE_POINT = "REMOVE_POINT"  # switched off (its records stay)
    RECORD = "RECORD"              # one reading or one filled checklist; out of range needs the action taken
    DAY = "DAY"                    # a site's day: each check, what was recorded, what is still due
    HISTORY = "HISTORY"            # every record between two dates (one site or all), with the failures counted


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    MISSING_SITE = "MISSING_SITE"
    UNKNOWN_POINT = "UNKNOWN_POINT"
    INVALID_NAME = "INVALID_NAME"
    INVALID_KIND = "INVALID_KIND"
    INVALID_RANGE = "INVALID_RANGE"
    INVALID_VALUE = "INVALID_VALUE"
    INVALID_DATE = "INVALID_DATE"
    ACTION_NEEDED = "ACTION_NEEDED"     # out of range / a "no" answer: say what was done about it


__all__ = ["ComplianceAction", "ReasonCode", "POINTS", "LOGS"]
