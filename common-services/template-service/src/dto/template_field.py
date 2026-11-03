# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of template rows and projections."""
from enum import Enum


class TemplateField(str, Enum):
    KEY = "key"
    LABEL = "label"
    PLACEHOLDERS = "placeholders"
    SUBJECT = "subject"
    TEXT = "text"
    BODIES = "bodies"
    ENABLED = "enabled"
    CHANNELS = "channels"
    TEMPLATE_KEY = "template_key"
