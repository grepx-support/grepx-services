# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for recognition-service vocabulary."""
import grepx_contracts as gc
from .recognition_action import RecognitionAction

EVENTS_TABLE = gc.event.EVENTS
BOOKINGS_TABLE = gc.booking.BOOKINGS
CERTIFICATES_TABLE = "certificates"
VOUCHERS_TABLE = "vouchers"
NOT_ENOUGH_CODES = "NOT_ENOUGH_CODES"
UNKNOWN_EVENT = "UNKNOWN_EVENT"

__all__ = ["RecognitionAction", "EVENTS_TABLE", "BOOKINGS_TABLE", "CERTIFICATES_TABLE", "VOUCHERS_TABLE", "NOT_ENOUGH_CODES", "UNKNOWN_EVENT"]
