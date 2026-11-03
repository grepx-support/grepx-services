# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why an auth request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    UNKNOWN_USER = "UNKNOWN_USER"
    INVALID_TOKEN = "INVALID_TOKEN"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
