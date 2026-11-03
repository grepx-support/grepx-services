"""Fields of notification rows."""
from enum import Enum


class NotificationField(str, Enum):
    TEMPLATE = "template"
    CHANNEL = "channel"
    RECIPIENT = "recipient"
    VALUES = "values"
    AUTO = "auto"
    SUBJECT = "subject"
    BODY = "body"
    DELIVERY = "delivery"
    ERROR = "error"
    SENT_AT = "sent_at"
