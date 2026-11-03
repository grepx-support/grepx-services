"""Why a person request is rejected (a profile plugin may raise its own codes)."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_NAME = "INVALID_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PHONE = "INVALID_PHONE"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    UNKNOWN_PERSON = "UNKNOWN_PERSON"
