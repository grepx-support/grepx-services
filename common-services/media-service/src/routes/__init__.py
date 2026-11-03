# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for media-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import MediaAction
from . import process
from . import delete

TABLE = "media_requests"
ROUTES = {
    MediaAction.PROCESS: process.handle,
    MediaAction.DELETE: delete.handle,
}
handle = ActionDispatcher(ROUTES, MediaAction, TABLE)
