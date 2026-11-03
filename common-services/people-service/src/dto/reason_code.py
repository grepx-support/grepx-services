# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a person request is rejected (a profile plugin may raise its own codes)."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_NAME = "INVALID_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PHONE = "INVALID_PHONE"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    UNKNOWN_PERSON = "UNKNOWN_PERSON"
