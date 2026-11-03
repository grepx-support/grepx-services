# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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
