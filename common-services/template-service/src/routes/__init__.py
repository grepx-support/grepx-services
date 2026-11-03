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
