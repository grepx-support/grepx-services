"""Actions notification-service accepts."""
from enum import Enum


class NotificationAction(str, Enum):
    SEND = "SEND"
    TEST_CHANNEL = "TEST_CHANNEL"
