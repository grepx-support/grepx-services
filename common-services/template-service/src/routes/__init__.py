# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for template-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import TemplateAction
from . import seed
from . import save
from . import reset

TABLE = "templates"
ROUTES = {
    TemplateAction.SEED: seed.handle,
    TemplateAction.SAVE: save.handle,
    TemplateAction.RESET: reset.handle,
}
handle = ActionDispatcher(ROUTES, TemplateAction, TABLE)
