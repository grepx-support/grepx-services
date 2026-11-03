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
