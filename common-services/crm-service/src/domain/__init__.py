# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""crm-service rules (pure)."""
from .activities import bucket, clean_activity
from .contacts import clean_contact
from .deals import clean_deal, close, move, reopen
from .insights import board, insights
from .pipeline import DEFAULT, clean_stages, stages_of

__all__ = ["DEFAULT", "board", "bucket", "clean_activity", "clean_contact", "clean_deal", "clean_stages", "close", "insights", "move", "reopen", "stages_of"]
