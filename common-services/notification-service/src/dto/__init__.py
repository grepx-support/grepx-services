"""Single import door for notification-service vocabulary."""
import grepx_contracts as gc
from .delivery import Delivery
from .notification_action import NotificationAction
from .notification_field import NotificationField
from .reason_code import ReasonCode

TEMPLATES_TABLE = gc.template.MESSAGE_TEMPLATES
SETTINGS_TABLE = gc.template.MESSAGE_SETTINGS

__all__ = ["Delivery", "NotificationAction", "NotificationField", "ReasonCode", "TEMPLATES_TABLE", "SETTINGS_TABLE"]
