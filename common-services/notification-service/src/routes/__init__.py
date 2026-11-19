# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for notification-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import NotificationAction
from . import devices
from . import retry
from . import send
from . import test_channel
from . import test_send

TABLE = "notifications"
ROUTES = {
    NotificationAction.SEND: send.handle,
    NotificationAction.TEST_CHANNEL: test_channel.handle,
    NotificationAction.TEST_SEND: test_send.handle,
    NotificationAction.RETRY: retry.handle,
    NotificationAction.REGISTER_DEVICE: devices.register,
    NotificationAction.FORGET_DEVICE: devices.forget,
    NotificationAction.PUSH_KEY: devices.push_key,
    NotificationAction.MARK_SEEN: devices.mark_seen,
}
handle = ActionDispatcher(ROUTES, NotificationAction, TABLE)
