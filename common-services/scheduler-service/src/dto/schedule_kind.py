# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""How often a schedule fires."""
from enum import Enum


class ScheduleKind(str, Enum):
    EVERY_MINUTES = "EVERY_MINUTES"
    DAILY_AT = "DAILY_AT"
