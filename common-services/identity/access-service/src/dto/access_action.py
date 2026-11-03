# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions access-service accepts."""
from enum import Enum


class AccessAction(str, Enum):
    SET_ROLE = "SET_ROLE"
    SET_STAFF_ROLE = "SET_STAFF_ROLE"
    SET_PERMISSION = "SET_PERMISSION"
    SAVE_ROLE = "SAVE_ROLE"
    DELETE_ROLE = "DELETE_ROLE"
    REGISTER_PERMISSION = "REGISTER_PERMISSION"
