"""Task lifecycle."""
from enum import Enum


class TaskState(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
