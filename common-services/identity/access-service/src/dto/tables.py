# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Tables access-service writes (projections) and reads."""
from enum import Enum


class Table(str, Enum):
    USER_ACCESS = "user_access"
    STAFF_ROLES = "staff_roles"
    PERMISSION_CATALOG = "permission_catalog"
