"""Actions campaign-service accepts."""
from enum import Enum


class CampaignAction(str, Enum):
    ANNOUNCE = "ANNOUNCE"
    INVITE = "INVITE"
    BROADCAST = "BROADCAST"
    PUBLISH_SOCIAL = "PUBLISH_SOCIAL"
    TEST_SOCIAL = "TEST_SOCIAL"
