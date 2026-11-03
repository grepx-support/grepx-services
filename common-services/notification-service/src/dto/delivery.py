"""Outcome of one delivery attempt."""
from enum import Enum


class Delivery(str, Enum):
    SENT = "SENT"
    LOGGED = "LOGGED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
