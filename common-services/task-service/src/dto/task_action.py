"""Actions task-service accepts."""
from enum import Enum


class TaskAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    CHANGE_STATUS = "CHANGE_STATUS"
    CLAIM = "CLAIM"
    DELETE = "DELETE"
