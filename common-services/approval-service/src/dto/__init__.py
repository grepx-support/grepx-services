# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names approval-service publishes."""
from enum import Enum

APPROVALS = "approvals"


class ApprovalAction(str, Enum):
    ASK = "ASK"              # hold a request until someone who may decide says yes: kind, ref, title, amount, details, perms, then / otherwise
    DECIDE = "DECIDE"        # yes or no, with a note; yes sends the held request (then), no sends otherwise (if any)
    WITHDRAW = "WITHDRAW"    # the one who asked takes it back while it waits


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    INVALID_KIND = "INVALID_KIND"
    INVALID_TITLE = "INVALID_TITLE"
    INVALID_REQUEST = "INVALID_REQUEST"        # a held request without table / service / fields, or aimed at this service
    NO_DECIDERS = "NO_DECIDERS"                # nobody in the business has a role that may decide it
    UNKNOWN_APPROVAL = "UNKNOWN_APPROVAL"
    ALREADY_DECIDED = "ALREADY_DECIDED"
    NOT_ALLOWED = "NOT_ALLOWED"                # this person's role may not decide it
    OWN_REQUEST = "OWN_REQUEST"                # you asked - someone else decides
    NOTE_REQUIRED = "NOTE_REQUIRED"            # a no needs a reason
    NOT_YOURS = "NOT_YOURS"                    # only the one who asked can withdraw


__all__ = ["APPROVALS", "ApprovalAction", "ApprovalState", "ReasonCode"]
