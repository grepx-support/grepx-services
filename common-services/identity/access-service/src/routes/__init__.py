"""Action routing for access-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import AccessAction
from . import set_role
from . import set_staff_role
from . import set_permission
from . import save_role
from . import delete_role
from . import register_permission

TABLE = "access_requests"
ROUTES = {
    AccessAction.SET_ROLE: set_role.handle,
    AccessAction.SET_STAFF_ROLE: set_staff_role.handle,
    AccessAction.SET_PERMISSION: set_permission.handle,
    AccessAction.SAVE_ROLE: save_role.handle,
    AccessAction.DELETE_ROLE: delete_role.handle,
    AccessAction.REGISTER_PERMISSION: register_permission.handle,
}
handle = ActionDispatcher(ROUTES, AccessAction, TABLE)
