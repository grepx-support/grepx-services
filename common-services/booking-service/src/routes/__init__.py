# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for booking-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import BookingAction
from . import interest
from . import book
from . import cancel
from . import move
from . import check_in
from . import mark

TABLE = "booking_requests"
ROUTES = {
    BookingAction.INTEREST: interest.handle,
    BookingAction.BOOK: book.handle,
    BookingAction.CANCEL: cancel.handle,
    BookingAction.MOVE: move.handle,
    BookingAction.CHECK_IN: check_in.handle,
    BookingAction.MARK: mark.handle,
}
handle = ActionDispatcher(ROUTES, BookingAction, TABLE)
