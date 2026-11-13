# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

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
    ATTACHMENTS = "attachments"      # [{name, mime, data_b64}] - files carried by channels that can (email)
