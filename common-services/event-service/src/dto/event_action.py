# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions event-service accepts."""
from enum import Enum


class EventAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    CLONE = "CLONE"
    SET_IMAGES = "SET_IMAGES"
    COMPLETE = "COMPLETE"
    REOPEN = "REOPEN"
