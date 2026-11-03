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
