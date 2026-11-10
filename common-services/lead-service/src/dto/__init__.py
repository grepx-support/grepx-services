# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names lead-service publishes."""
from enum import Enum


class LeadAction(str, Enum):
    SUBMIT = "SUBMIT"          # from the public website
    SET_STATUS = "SET_STATUS"  # the operator's follow-up


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    WON = "won"
    LOST = "lost"


class ReasonCode(str, Enum):
    INVALID_NAME = "INVALID_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_STATUS = "INVALID_STATUS"
    UNKNOWN_LEAD = "UNKNOWN_LEAD"
    SPAM = "SPAM"


TABLE = "leads"

__all__ = ["LeadAction", "LeadStatus", "ReasonCode", "TABLE"]
