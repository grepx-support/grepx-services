# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names ai-service publishes."""
from enum import Enum

AI_USAGE = "ai_usage"


class AiAction(str, Enum):
    ASK = "ASK"            # feature, instructions, question, data (the business's own facts), limit -> answer
    USAGE = "USAGE"        # this month's calls and the limit


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    NO_QUESTION = "NO_QUESTION"
    AI_OFF = "AI_OFF"                  # the business has not switched AI on
    NO_KEY = "NO_KEY"                  # the platform has no model key yet
    LIMIT_REACHED = "LIMIT_REACHED"    # this month's calls are used up
    MODEL_FAILED = "MODEL_FAILED"      # the model did not answer (network, overload)


__all__ = ["AI_USAGE", "AiAction", "ReasonCode"]
