"""Tables access-service writes (projections) and reads."""
from enum import Enum


class Table(str, Enum):
    USER_ACCESS = "user_access"
    STAFF_ROLES = "staff_roles"
    PERMISSION_CATALOG = "permission_catalog"
