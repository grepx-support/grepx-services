# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for payroll-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import PayrollAction
from . import adjust, finalise, month, run, set_settings, settings

TABLE = "payroll_requests"
ROUTES = {
    PayrollAction.SETTINGS: settings.handle,
    PayrollAction.SET_SETTINGS: set_settings.handle,
    PayrollAction.ADJUST: adjust.handle,
    PayrollAction.REMOVE_ADJUSTMENT: adjust.remove,
    PayrollAction.RUN: run.handle,
    PayrollAction.FINALISE: finalise.handle,
    PayrollAction.MONTH: month.handle,
}
handle = ActionDispatcher(ROUTES, PayrollAction, TABLE)
