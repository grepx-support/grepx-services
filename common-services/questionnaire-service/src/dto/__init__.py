# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for questionnaire-service vocabulary."""
from .questionnaire_action import QuestionnaireAction
from .questionnaire_field import QuestionnaireField

INVALID_ANSWERS = "INVALID_ANSWERS"
NOT_CONFIGURED = "NOT_CONFIGURED"   # no plugins.questionnaire in this deployment

__all__ = ["QuestionnaireAction", "QuestionnaireField", "INVALID_ANSWERS", "NOT_CONFIGURED"]
