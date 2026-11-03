# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a task request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_TASK = "UNKNOWN_TASK"
    NOT_ALLOWED = "NOT_ALLOWED"
    INVALID_STATE = "INVALID_STATE"
    ALREADY_ASSIGNED = "ALREADY_ASSIGNED"
