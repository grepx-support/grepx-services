"""Actions settings-service accepts."""
from enum import Enum


class SettingsAction(str, Enum):
    SET = "SET"
    DELETE = "DELETE"
