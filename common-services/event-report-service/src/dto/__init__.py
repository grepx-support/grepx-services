# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for event-report-service vocabulary."""
import grepx_contracts as gc
from .event_report_action import EventReportAction

REPORTS_TABLE = "event_reports"
EVENTS_TABLE, BOOKINGS_TABLE, SLOTS_TABLE = gc.event.EVENTS, gc.booking.BOOKINGS, gc.slot.SLOTS
NOTIFICATIONS_TABLE, TASKS_TABLE = gc.notification.NOTIFICATIONS, gc.task.TASKS
RETRO_FIELDS = ("went_well", "to_improve", "actions", "notes", "rating")
UNKNOWN_EVENT, INVALID_RATING = "UNKNOWN_EVENT", "INVALID_RATING"

__all__ = ["EventReportAction", "REPORTS_TABLE", "EVENTS_TABLE", "BOOKINGS_TABLE", "SLOTS_TABLE", "NOTIFICATIONS_TABLE", "TASKS_TABLE", "RETRO_FIELDS", "UNKNOWN_EVENT", "INVALID_RATING"]
