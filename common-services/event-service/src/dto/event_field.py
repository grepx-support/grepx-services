# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Fields of event requests and the events projection."""
from enum import Enum


class EventField(str, Enum):
    EVENT_ID = "event_id"
    TITLE = "title"
    VENUE = "venue"
    EVENT_DATE = "event_date"
    TIME_SLOT = "time_slot"
    DESCRIPTION = "description"
    CAPACITY = "capacity"
    IMAGES = "images"
    IMAGE_URL = "image_url"
    STATE = "state"
    COMPLETED_AT = "completed_at"
    COMPLETED_BY = "completed_by"
    VOUCHER = "voucher"
    SLOT_PLAN = "slot_plan"
    SOURCE_EVENT_ID = "source_event_id"
    COPY_SLOTS = "copy_slots"
    APPLY_CHECKLIST = "apply_checklist"
    ASSIGNEE = "assignee"
    ACTOR_ID = "actor_id"
    TENANT_ID = "tenant_id"
    CREATED = "created"
