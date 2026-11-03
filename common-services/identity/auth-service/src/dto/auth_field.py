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
