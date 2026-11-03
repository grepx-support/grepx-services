"""Actions recognition-service accepts."""
from enum import Enum


class RecognitionAction(str, Enum):
    ISSUE = "ISSUE"
