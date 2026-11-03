# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for auth-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import AuthAction
from . import register
from . import login
from . import change_password
from . import set_password
from . import reset_request
from . import reset_confirm
from . import login_external
from . import link_external

TABLE = "auth_requests"
ROUTES = {
    AuthAction.REGISTER: register.handle,
    AuthAction.LOGIN: login.handle,
    AuthAction.CHANGE_PASSWORD: change_password.handle,
    AuthAction.SET_PASSWORD: set_password.handle,
    AuthAction.RESET_REQUEST: reset_request.handle,
    AuthAction.RESET_CONFIRM: reset_confirm.handle,
    AuthAction.LOGIN_EXTERNAL: login_external.handle,
    AuthAction.LINK_EXTERNAL: link_external.handle,
}
handle = ActionDispatcher(ROUTES, AuthAction, TABLE)
