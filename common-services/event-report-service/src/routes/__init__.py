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
