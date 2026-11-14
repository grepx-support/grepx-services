# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for leave-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import LeaveAction
from . import balances, calendar, cancel, decide, request, save_type

TABLE = "leave_requests"
ROUTES = {
    LeaveAction.SAVE_TYPE: save_type.handle,
    LeaveAction.REQUEST: request.handle,
    LeaveAction.DECIDE: decide.handle,
    LeaveAction.CANCEL: cancel.handle,
    LeaveAction.BALANCES: balances.handle,
    LeaveAction.CALENDAR: calendar.handle,
}
handle = ActionDispatcher(ROUTES, LeaveAction, TABLE)
