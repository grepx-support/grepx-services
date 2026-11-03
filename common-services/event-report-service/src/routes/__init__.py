# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for event-report-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import EventReportAction
from . import snapshot
from . import save_retro

TABLE = "event_report_requests"
ROUTES = {
    EventReportAction.SNAPSHOT: snapshot.handle,
    EventReportAction.SAVE_RETRO: save_retro.handle,
}
handle = ActionDispatcher(ROUTES, EventReportAction, TABLE)
