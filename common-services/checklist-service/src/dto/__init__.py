"""Single import door for checklist-service vocabulary."""
import grepx_contracts as gc
from .checklist_action import ChecklistAction
from .checklist_field import ChecklistField
from .reason_code import ReasonCode

TEMPLATES_TABLE = "checklist_templates"
TASKS_TABLE = gc.task.TASKS
TASK_REQUESTS = gc.task.REQUESTS
TASK_SERVICE = gc.task.SERVICE
ASSIGNEE_FIELDS = ("assignee_id", "assignee_name", "assignee_email", "assignee_phone")

__all__ = ["ChecklistAction", "ChecklistField", "ReasonCode", "TEMPLATES_TABLE", "TASKS_TABLE", "TASK_REQUESTS", "TASK_SERVICE", "ASSIGNEE_FIELDS"]
