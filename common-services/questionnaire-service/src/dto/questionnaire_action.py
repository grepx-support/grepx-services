"""Actions questionnaire-service accepts."""
from enum import Enum


class QuestionnaireAction(str, Enum):
    CHECK = "CHECK"
    CHAT = "CHAT"
    CRITERIA = "CRITERIA"
