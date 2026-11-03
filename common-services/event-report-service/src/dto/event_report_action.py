# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions event-report-service accepts."""
from enum import Enum


class EventReportAction(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    SAVE_RETRO = "SAVE_RETRO"
