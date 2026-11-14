# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What an image is for — decides its processing profile."""
from enum import Enum


class MediaKind(str, Enum):
    PICTURE = "picture"
    AVATAR = "avatar"
    LOGO = "logo"           # a business or organisation mark printed on documents (transparency kept, PNG)
