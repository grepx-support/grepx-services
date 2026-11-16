# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names signup-service publishes."""
from enum import Enum


class SignupAction(str, Enum):
    CHECK = "CHECK"                  # is this short name free? (changes nothing)
    START = "START"                  # the owner's details: hold the short name, send the email link and the phone code
    CONFIRM_EMAIL = "CONFIRM_EMAIL"  # the link from the email was opened
    CONFIRM_PHONE = "CONFIRM_PHONE"  # the 6-digit code from the phone was typed
    RESEND = "RESEND"                # a new email link or phone code (at most one a minute)
    BEGIN_SETUP = "BEGIN_SETUP"      # both confirmed: exactly one caller may now set the business up
    ACTIVATE = "ACTIVATE"            # the business exists: its short name now points to it
    FAIL = "FAIL"                    # setting up did not work: the short name is free again
    SET_ADDRESS = "SET_ADDRESS"      # the platform operator gives a business (or changes) its short name


class SignupStage(str, Enum):
    PENDING = "pending"          # waiting for the email link and / or the phone code
    VERIFIED = "verified"        # both confirmed, not set up yet
    SETTING_UP = "setting_up"    # one caller is creating the business
    ACTIVE = "active"            # the business exists
    FAILED = "failed"            # could not be set up (reason kept)
    REPLACED = "replaced"        # the same email started again


class ReasonCode(str, Enum):
    INVALID_BUSINESS_NAME = "INVALID_BUSINESS_NAME"
    INVALID_SLUG = "INVALID_SLUG"
    RESERVED_SLUG = "RESERVED_SLUG"
    SLUG_TAKEN = "SLUG_TAKEN"
    INVALID_NAME = "INVALID_NAME"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PHONE = "INVALID_PHONE"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    MISSING_PASSWORD = "MISSING_PASSWORD"
    SPAM = "SPAM"
    UNKNOWN_SIGNUP = "UNKNOWN_SIGNUP"
    SIGNUP_EXPIRED = "SIGNUP_EXPIRED"
    WRONG_LINK = "WRONG_LINK"
    CODE_EXPIRED = "CODE_EXPIRED"
    TOO_MANY_TRIES = "TOO_MANY_TRIES"
    TOO_SOON = "TOO_SOON"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_SETTING_UP = "NOT_SETTING_UP"
    ALREADY_DONE = "ALREADY_DONE"
    MISSING_BUSINESS = "MISSING_BUSINESS"


SIGNUPS, ADDRESSES = "signups", "addresses"

__all__ = ["SignupAction", "SignupStage", "ReasonCode", "SIGNUPS", "ADDRESSES"]
