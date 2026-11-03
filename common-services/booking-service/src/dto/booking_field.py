"""Fields of booking requests and the bookings projection."""
from enum import Enum


class BookingField(str, Enum):
    BOOKING_ID = "booking_id"
    EVENT_ID = "event_id"
    PERSON_ID = "person_id"
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    STATE = "state"
    SLOT_ID = "slot_id"
    SLOT_START = "slot_start"
    SLOT_END = "slot_end"
    SOURCE = "source"
    REMINDED_AT = "reminded_at"
    OVERRIDE_CAPACITY = "override_capacity"
    TENANT_ID = "tenant_id"
    CREATED = "created"
    UPDATED = "updated"
