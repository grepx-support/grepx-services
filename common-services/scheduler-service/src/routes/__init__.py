# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for scheduler-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import SchedulerAction
from . import register
from . import cancel

TABLE = "schedule_requests"
ROUTES = {
    SchedulerAction.REGISTER: register.handle,
    SchedulerAction.CANCEL: cancel.handle,
}
handle = ActionDispatcher(ROUTES, SchedulerAction, TABLE)
