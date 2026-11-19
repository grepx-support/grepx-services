# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions notification-service accepts."""
from enum import Enum


class NotificationAction(str, Enum):
    SEND = "SEND"
    TEST_CHANNEL = "TEST_CHANNEL"
    TEST_SEND = "TEST_SEND"          # send a short test message on one channel to one address (the Integrations page)
    RETRY = "RETRY"                  # try a failed send again now (the Outbox's "Try again")
    REGISTER_DEVICE = "REGISTER_DEVICE"  # a person's phone / browser agreed to notifications: its Web Push subscription
    FORGET_DEVICE = "FORGET_DEVICE"      # notifications switched off on a device (or it stopped answering)
    PUSH_KEY = "PUSH_KEY"                # the public key browsers subscribe with (the pair is made the first time)
    MARK_SEEN = "MARK_SEEN"              # the person opened the bell: everything up to now is read
