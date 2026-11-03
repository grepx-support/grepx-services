# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for campaign-service vocabulary."""
import grepx_contracts as gc
from .campaign_action import CampaignAction

ACCESS_TABLE = gc.access.USER_ACCESS
EVENTS_TABLE, BOOKINGS_TABLE, CAMPAIGNS_TABLE = gc.event.EVENTS, gc.booking.BOOKINGS, "campaigns"
UNKNOWN_EVENT, UNKNOWN_AUDIENCE, MISSING_TEXT = "UNKNOWN_EVENT", "UNKNOWN_AUDIENCE", "MISSING_TEXT"

__all__ = ["CampaignAction", "ACCESS_TABLE", "EVENTS_TABLE", "BOOKINGS_TABLE", "CAMPAIGNS_TABLE", "UNKNOWN_EVENT", "UNKNOWN_AUDIENCE", "MISSING_TEXT"]
