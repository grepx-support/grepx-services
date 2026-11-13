# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a notification is rejected outright."""
from enum import Enum


class ReasonCode(str, Enum):
    UNKNOWN_TEMPLATE = "UNKNOWN_TEMPLATE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CHECK_FAILED = "CHECK_FAILED"
    MISSING_RECIPIENT = "MISSING_RECIPIENT"
    UNKNOWN_CHANNEL = "UNKNOWN_CHANNEL"
    ATTACHMENT_TOO_LARGE = "ATTACHMENT_TOO_LARGE"
    NOT_FAILED = "NOT_FAILED"
    ALREADY_RETRIED = "ALREADY_RETRIED"
