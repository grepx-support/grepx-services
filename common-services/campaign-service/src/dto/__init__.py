"""Single import door for campaign-service vocabulary."""
import grepx_contracts as gc
from .campaign_action import CampaignAction

ACCESS_TABLE = gc.access.USER_ACCESS
EVENTS_TABLE, BOOKINGS_TABLE, CAMPAIGNS_TABLE = gc.event.EVENTS, gc.booking.BOOKINGS, "campaigns"
UNKNOWN_EVENT, UNKNOWN_AUDIENCE, MISSING_TEXT = "UNKNOWN_EVENT", "UNKNOWN_AUDIENCE", "MISSING_TEXT"

__all__ = ["CampaignAction", "ACCESS_TABLE", "EVENTS_TABLE", "BOOKINGS_TABLE", "CAMPAIGNS_TABLE", "UNKNOWN_EVENT", "UNKNOWN_AUDIENCE", "MISSING_TEXT"]
