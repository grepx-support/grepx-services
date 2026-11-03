# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for referral-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import ReferralAction
from . import score

TABLE = "referral_events"
ROUTES = {
    ReferralAction.SCORE: score.handle,
}
handle = ActionDispatcher(ROUTES, ReferralAction, TABLE)
