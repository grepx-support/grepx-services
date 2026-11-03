"""Actions template-service accepts."""
from enum import Enum


class TemplateAction(str, Enum):
    SEED = "SEED"
    SAVE = "SAVE"
    RESET = "RESET"
