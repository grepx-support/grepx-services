# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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
