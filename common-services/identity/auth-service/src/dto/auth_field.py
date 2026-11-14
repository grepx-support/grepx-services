# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of auth_requests rows."""
from enum import Enum


class AuthField(str, Enum):
    USER_ID = "user_id"
    EMAIL = "email"
    PASSWORD_ENC = "password_enc"
    CURRENT_ENC = "current_enc"
    TOKEN = "token"
    TOKEN_ENC = "token_enc"
    TEMP_PASSWORD_ENC = "temp_password_enc"
    REMEMBER = "remember"
    TENANT_ID = "tenant_id"
    ROLE = "role"
    EXPIRES_HOURS = "expires_hours"
    LINK_BASE = "link_base"
    PROVIDER = "provider"
    ID_TOKEN_ENC = "id_token_enc"
    REGISTERED = "registered"
    NAME = "name"
    TWO_STEP = "two_step"                 # LOGIN answer: true = a code is needed (see LOGIN_CODE)
    CHALLENGE_ENC = "challenge_enc"       # sealed, 5 minutes: proves the password (or provider) step passed
    CODE = "code"                         # six digits from the app, or a recovery code
    SECRET_ENC = "secret_enc"             # TWO_STEP_START answer: the key to type into the app
    APP_LINK_ENC = "app_link_enc"         # TWO_STEP_START answer: otpauth:// link for the QR code
    RECOVERY_ENC = "recovery_enc"         # TWO_STEP_ENABLE answer: the ten recovery codes, shown once
    ISSUER = "issuer"                     # the name shown in the authenticator app
