"""Action routing for task-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import TaskAction
from . import create
from . import update
from . import change_status
from . import claim
from . import delete

TABLE = "task_requests"
ROUTES = {
    TaskAction.CREATE: create.handle,
    TaskAction.UPDATE: update.handle,
    TaskAction.CHANGE_STATUS: change_status.handle,
    TaskAction.CLAIM: claim.handle,
    TaskAction.DELETE: delete.handle,
}
handle = ActionDispatcher(ROUTES, TaskAction, TABLE)
