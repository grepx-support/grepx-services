"""Action routing for checklist-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import ChecklistAction
from . import seed_template
from . import apply
from . import remove

TABLE = "checklist_requests"
ROUTES = {
    ChecklistAction.SEED_TEMPLATE: seed_template.handle,
    ChecklistAction.APPLY: apply.handle,
    ChecklistAction.REMOVE: remove.handle,
}
handle = ActionDispatcher(ROUTES, ChecklistAction, TABLE)
