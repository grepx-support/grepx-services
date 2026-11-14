# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for employee-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import EmployeeAction
from . import end, remove_document, save, set_document, team

TABLE = "employee_requests"
ROUTES = {
    EmployeeAction.SAVE: save.handle,
    EmployeeAction.SET_DOCUMENT: set_document.handle,
    EmployeeAction.REMOVE_DOCUMENT: remove_document.handle,
    EmployeeAction.END: end.handle,
    EmployeeAction.TEAM: team.handle,
}
handle = ActionDispatcher(ROUTES, EmployeeAction, TABLE)
