# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for event-service vocabulary."""
import grepx_contracts as gc
from .event_action import EventAction
from .event_field import EventField
from .event_state import EventState
from .reason_code import ReasonCode

EVENTS_TABLE = "events"
SLOTS_TABLE = gc.slot.SLOTS
SLOT_REQUESTS, SLOT_SERVICE = gc.slot.REQUESTS, gc.slot.SERVICE
CHECKLIST_REQUESTS, CHECKLIST_SERVICE = gc.checklist.REQUESTS, gc.checklist.SERVICE
IMAGE_LIMIT = 3
DETAIL_FIELDS = (EventField.TITLE, EventField.VENUE, EventField.EVENT_DATE, EventField.TIME_SLOT, EventField.DESCRIPTION, EventField.CAPACITY)

__all__ = ["EventAction", "EventField", "EventState", "ReasonCode", "EVENTS_TABLE", "SLOTS_TABLE", "SLOT_REQUESTS", "SLOT_SERVICE",
           "CHECKLIST_REQUESTS", "CHECKLIST_SERVICE", "IMAGE_LIMIT", "DETAIL_FIELDS"]
