# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for recognition-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import RecognitionAction
from . import issue

TABLE = "recognition_requests"
ROUTES = {
    RecognitionAction.ISSUE: issue.handle,
}
handle = ActionDispatcher(ROUTES, RecognitionAction, TABLE)
