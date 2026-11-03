"""Single import door for task-service vocabulary."""
from .reason_code import ReasonCode
from .task_action import TaskAction
from .task_field import TaskField
from .task_state import TaskState

TASKS_TABLE = "tasks"
TICKS_TABLE = "ticks"
EDITABLE = (TaskField.TITLE, TaskField.DESCRIPTION, TaskField.DUE_AT, TaskField.ASSIGNEE_ID, TaskField.ASSIGNEE_NAME,
            TaskField.ASSIGNEE_EMAIL, TaskField.ASSIGNEE_PHONE, TaskField.REF_TYPE, TaskField.REF_ID, TaskField.REF_LABEL,
            TaskField.IMPORTANT, TaskField.REMIND, TaskField.PHASE, TaskField.STATE, TaskField.CHECKLIST)

__all__ = ["ReasonCode", "TaskAction", "TaskField", "TaskState", "TASKS_TABLE", "TICKS_TABLE", "EDITABLE"]
