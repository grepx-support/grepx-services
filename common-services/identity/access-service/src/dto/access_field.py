# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of access_requests and the user_access / staff_roles projections."""
from enum import Enum


class AccessField(str, Enum):
    USER_ID = "user_id"
    ACTOR_ID = "actor_id"
    ROLE = "role"
    STAFF_ROLE_ID = "staff_role_id"
    PERM = "perm"
    ENABLED = "enabled"
    PERMS = "perms"
    EFFECTIVE = "effective"
    NAME = "name"
    DESCRIPTION = "description"
    ROLE_ID = "role_id"
    TENANT_ID = "tenant_id"
    LABEL = "label"
