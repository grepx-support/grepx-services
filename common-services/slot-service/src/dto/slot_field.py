"""Fields of slot requests and the slots projection."""
from enum import Enum


class SlotField(str, Enum):
    SLOT_ID = "slot_id"
    EVENT_ID = "event_id"
    STARTS_AT = "starts_at"
    ENDS_AT = "ends_at"
    CAPACITY = "capacity"
    PLAN = "plan"
    SLOTS = "slots"
    VALUE = "value"
    DELTA = "delta"
    BOOKED = "booked"
    TENANT_ID = "tenant_id"
