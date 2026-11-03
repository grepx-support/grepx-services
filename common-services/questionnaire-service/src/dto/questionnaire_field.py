"""Fields of questionnaire_requests rows."""
from enum import Enum


class QuestionnaireField(str, Enum):
    ANSWERS = "answers"
    ELIGIBLE = "eligible"
    REASONS = "reasons"
    NOTES = "notes"
    STATE = "state"
    MESSAGE = "message"
    REPLY = "reply"
    CRITERIA = "criteria"
