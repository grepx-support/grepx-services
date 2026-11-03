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
