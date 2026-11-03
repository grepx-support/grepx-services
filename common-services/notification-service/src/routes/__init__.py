# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for notification-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import NotificationAction
from . import send
from . import test_channel

TABLE = "notifications"
ROUTES = {
    NotificationAction.SEND: send.handle,
    NotificationAction.TEST_CHANNEL: test_channel.handle,
}
handle = ActionDispatcher(ROUTES, NotificationAction, TABLE)
