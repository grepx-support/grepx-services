# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for event-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import EventAction
from . import create
from . import update
from . import clone
from . import set_images
from . import complete
from . import reopen

TABLE = "event_requests"
ROUTES = {
    EventAction.CREATE: create.handle,
    EventAction.UPDATE: update.handle,
    EventAction.CLONE: clone.handle,
    EventAction.SET_IMAGES: set_images.handle,
    EventAction.COMPLETE: complete.handle,
    EventAction.REOPEN: reopen.handle,
}
handle = ActionDispatcher(ROUTES, EventAction, TABLE)
