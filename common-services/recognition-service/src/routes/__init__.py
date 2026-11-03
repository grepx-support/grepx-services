"""Action routing for recognition-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import RecognitionAction
from . import issue

TABLE = "recognition_requests"
ROUTES = {
    RecognitionAction.ISSUE: issue.handle,
}
handle = ActionDispatcher(ROUTES, RecognitionAction, TABLE)
