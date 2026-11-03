# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions people-service accepts."""
from enum import Enum


class PersonAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SET_PHOTO = "SET_PHOTO"
    RESET_CAL_TOKEN = "RESET_CAL_TOKEN"
