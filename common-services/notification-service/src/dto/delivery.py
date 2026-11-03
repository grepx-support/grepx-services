# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Outcome of one delivery attempt."""
from enum import Enum


class Delivery(str, Enum):
    SENT = "SENT"
    LOGGED = "LOGGED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
