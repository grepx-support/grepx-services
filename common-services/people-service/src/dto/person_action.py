"""Actions people-service accepts."""
from enum import Enum


class PersonAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SET_PHOTO = "SET_PHOTO"
    RESET_CAL_TOKEN = "RESET_CAL_TOKEN"
