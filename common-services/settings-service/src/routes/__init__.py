# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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
