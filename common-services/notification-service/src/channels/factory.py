# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ChannelFactory — picks the real channel, or the log fallback when it is not configured."""
from __future__ import annotations

from .base import Channel
from .log_channel import LogChannel
from .smtp_email import SmtpEmailChannel
from .twilio import TwilioSmsChannel, TwilioWhatsAppChannel


class ChannelFactory:
    """Channels are built from the environment, overridden by what admins saved on the Integrations page
    (settings-service; secrets sealed with the platform key)."""
    def __init__(self, channels: list[Channel] | None = None):
        self.fixed = {c.name: c for c in channels} if channels else None
        self.fallback = LogChannel()

    def get(self, name: str, settings: dict | None = None) -> tuple[Channel, bool]:
        """(channel, is_real)."""
        if self.fixed is not None:
            channel = self.fixed.get(name)
        else:
            import os
            env = {**os.environ, **{k: v for k, v in (settings or {}).items() if v not in (None, "")}}
            channel = {c.name: c for c in (SmtpEmailChannel(env), TwilioSmsChannel(env), TwilioWhatsAppChannel(env))}.get(name)
        return (channel, True) if channel and channel.configured() else (self.fallback, False)
