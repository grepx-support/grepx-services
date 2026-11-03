"""Actions audit-log-service accepts."""
from enum import Enum


class AuditLogAction(str, Enum):
    RECORD = "RECORD"
