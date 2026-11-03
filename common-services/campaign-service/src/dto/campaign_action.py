# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions campaign-service accepts."""
from enum import Enum


class CampaignAction(str, Enum):
    ANNOUNCE = "ANNOUNCE"
    INVITE = "INVITE"
    BROADCAST = "BROADCAST"
    PUBLISH_SOCIAL = "PUBLISH_SOCIAL"
    TEST_SOCIAL = "TEST_SOCIAL"
