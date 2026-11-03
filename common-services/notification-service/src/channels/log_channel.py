"""Console fallback used when a real channel is not configured (dev and demos)."""
import logging

from .base import Channel

logger = logging.getLogger(__name__)


class LogChannel(Channel):
    name = "log"

    def configured(self) -> bool:
        return True

    def send(self, recipient, subject, body, html=None) -> None:
        logger.info("[message to %s] %s", recipient[-4:], subject)
