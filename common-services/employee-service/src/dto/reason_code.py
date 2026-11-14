# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why employee-service refuses a request."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_EMPLOYEE = "UNKNOWN_EMPLOYEE"
    INVALID_NAME = "INVALID_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_DATE = "INVALID_DATE"
    INVALID_SITE = "INVALID_SITE"
    INVALID_PAY = "INVALID_PAY"
    INVALID_DOCUMENT = "INVALID_DOCUMENT"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    ALREADY_ENDED = "ALREADY_ENDED"
