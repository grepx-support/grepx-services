# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a template request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_TEMPLATE = "UNKNOWN_TEMPLATE"
    UNKNOWN_PLACEHOLDER = "UNKNOWN_PLACEHOLDER"
    UNKNOWN_CHANNEL = "UNKNOWN_CHANNEL"
