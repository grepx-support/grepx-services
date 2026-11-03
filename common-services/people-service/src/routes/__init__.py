# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for people-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import PersonAction
from . import create, reset_cal_token, set_photo, update

TABLE = "people_requests"
ROUTES = {
    PersonAction.CREATE: create.handle,
    PersonAction.UPDATE: update.handle,
    PersonAction.SET_PHOTO: set_photo.handle,
    PersonAction.RESET_CAL_TOKEN: reset_cal_token.handle,
}
handle = ActionDispatcher(ROUTES, PersonAction, TABLE)
