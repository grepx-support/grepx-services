# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for referral-service vocabulary."""
from .referral_action import ReferralAction

SCORES_TABLE = "referral_scores"

__all__ = ["ReferralAction", "SCORES_TABLE"]
