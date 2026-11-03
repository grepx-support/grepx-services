"""Action routing for settings-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import SettingsAction
from . import set
from . import delete

TABLE = "settings_requests"
ROUTES = {
    SettingsAction.SET: set.handle,
    SettingsAction.DELETE: delete.handle,
}
handle = ActionDispatcher(ROUTES, SettingsAction, TABLE)
