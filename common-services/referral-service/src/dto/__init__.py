"""Single import door for referral-service vocabulary."""
from .referral_action import ReferralAction

SCORES_TABLE = "referral_scores"

__all__ = ["ReferralAction", "SCORES_TABLE"]
