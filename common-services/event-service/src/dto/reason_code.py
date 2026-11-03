# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why an event request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_DATE = "INVALID_DATE"
    INVALID_CAPACITY = "INVALID_CAPACITY"
    UNKNOWN_EVENT = "UNKNOWN_EVENT"
    TOO_MANY_IMAGES = "TOO_MANY_IMAGES"
    TOO_EARLY = "TOO_EARLY"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    NOT_COMPLETED = "NOT_COMPLETED"
