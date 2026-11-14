# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions auth-service accepts."""
from enum import Enum


class AuthAction(str, Enum):
    REGISTER = "REGISTER"
    LOGIN = "LOGIN"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    SET_PASSWORD = "SET_PASSWORD"
    RESET_REQUEST = "RESET_REQUEST"
    RESET_CONFIRM = "RESET_CONFIRM"
    LOGIN_EXTERNAL = "LOGIN_EXTERNAL"
    LINK_EXTERNAL = "LINK_EXTERNAL"
    LOGIN_CODE = "LOGIN_CODE"             # second step of a login: the app's code (or a recovery code)
    TWO_STEP_START = "TWO_STEP_START"     # make a new authenticator key for the person
    TWO_STEP_ENABLE = "TWO_STEP_ENABLE"   # first code matched: two-step login is on
    TWO_STEP_DISABLE = "TWO_STEP_DISABLE" # off again (password and a code needed)
    TWO_STEP_STATUS = "TWO_STEP_STATUS"   # on / off, recovery codes left, linked providers
