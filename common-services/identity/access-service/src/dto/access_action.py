"""Actions access-service accepts."""
from enum import Enum


class AccessAction(str, Enum):
    SET_ROLE = "SET_ROLE"
    SET_STAFF_ROLE = "SET_STAFF_ROLE"
    SET_PERMISSION = "SET_PERMISSION"
    SAVE_ROLE = "SAVE_ROLE"
    DELETE_ROLE = "DELETE_ROLE"
    REGISTER_PERMISSION = "REGISTER_PERMISSION"
