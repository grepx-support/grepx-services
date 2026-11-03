# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of media requests and the media projection."""
from enum import Enum


class MediaField(str, Enum):
    MEDIA_ID = "media_id"
    STAGED_KEY = "staged_key"
    KIND = "kind"
    OWNER_ID = "owner_id"
    KEY = "key"
    CONTENT_TYPE = "content_type"
    SIZE = "size"
    WIDTH = "width"
    HEIGHT = "height"
