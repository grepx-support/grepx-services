"""Actions checklist-service accepts."""
from enum import Enum


class ChecklistAction(str, Enum):
    SEED_TEMPLATE = "SEED_TEMPLATE"
    APPLY = "APPLY"
    REMOVE = "REMOVE"
