"""Action routing for referral-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import ReferralAction
from . import score

TABLE = "referral_events"
ROUTES = {
    ReferralAction.SCORE: score.handle,
}
handle = ActionDispatcher(ROUTES, ReferralAction, TABLE)
