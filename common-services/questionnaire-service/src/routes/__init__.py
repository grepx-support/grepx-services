"""Action routing for questionnaire-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import QuestionnaireAction
from . import check
from . import chat
from . import criteria

TABLE = "questionnaire_requests"
ROUTES = {
    QuestionnaireAction.CHECK: check.handle,
    QuestionnaireAction.CHAT: chat.handle,
    QuestionnaireAction.CRITERIA: criteria.handle,
}
handle = ActionDispatcher(ROUTES, QuestionnaireAction, TABLE)
