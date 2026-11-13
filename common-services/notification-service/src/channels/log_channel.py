# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Console fallback used when a real channel is not configured (dev and demos)."""
import logging

from .base import Channel

logger = logging.getLogger(__name__)


class LogChannel(Channel):
    name = "log"

    def configured(self) -> bool:
        return True

    def send(self, recipient, subject, body, html=None, attachments=None) -> None:
        logger.info("[message to %s] %s", recipient[-4:], subject)
