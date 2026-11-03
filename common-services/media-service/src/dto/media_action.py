"""Actions media-service accepts."""
from enum import Enum


class MediaAction(str, Enum):
    PROCESS = "PROCESS"
    DELETE = "DELETE"
