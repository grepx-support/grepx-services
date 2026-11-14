# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for roster-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import RosterAction
from . import clock, copy_week, publish_week, remove_shift, save_shift, set_pin, week

TABLE = "roster_requests"
ROUTES = {
    RosterAction.SAVE_SHIFT: save_shift.handle,
    RosterAction.REMOVE_SHIFT: remove_shift.handle,
    RosterAction.COPY_WEEK: copy_week.handle,
    RosterAction.PUBLISH_WEEK: publish_week.handle,
    RosterAction.WEEK: week.handle,
    RosterAction.SET_PIN: set_pin.handle,
    RosterAction.CLOCK: clock.handle,
}
handle = ActionDispatcher(ROUTES, RosterAction, TABLE)
