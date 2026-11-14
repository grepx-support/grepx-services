# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for compliance-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import ComplianceAction
from . import day, history, record, save_point

TABLE = "compliance_requests"
ROUTES = {
    ComplianceAction.SAVE_POINT: save_point.handle,
    ComplianceAction.REMOVE_POINT: save_point.remove,
    ComplianceAction.RECORD: record.handle,
    ComplianceAction.DAY: day.handle,
    ComplianceAction.HISTORY: history.handle,
}
handle = ActionDispatcher(ROUTES, ComplianceAction, TABLE)
