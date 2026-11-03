# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a media request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FILE = "MISSING_FILE"
    TOO_LARGE = "TOO_LARGE"
    NOT_AN_IMAGE = "NOT_AN_IMAGE"
    UNKNOWN_KIND = "UNKNOWN_KIND"
    UNKNOWN_MEDIA = "UNKNOWN_MEDIA"
