"""What an image is for — decides its processing profile."""
from enum import Enum


class MediaKind(str, Enum):
    PICTURE = "picture"
    AVATAR = "avatar"
