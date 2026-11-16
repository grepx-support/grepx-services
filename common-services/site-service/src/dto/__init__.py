# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names site-service publishes."""
from enum import Enum


class SiteAction(str, Enum):
    SAVE = "SAVE"          # the business's page as its owner (or platform support) wrote it; replaces the one before


class Section(str, Enum):
    """The parts of the page an owner can switch on or off (in this order on the page)."""
    OFFERS = "offers"
    HIGHLIGHTS = "highlights"
    BRANDS = "brands"
    VIDEOS = "videos"
    SOCIAL = "social"
    VISIT = "visit"
    SIGN_IN = "sign_in"


class ReasonCode(str, Enum):
    MISSING_BUSINESS = "MISSING_BUSINESS"
    INVALID_PAGE = "INVALID_PAGE"
    INVALID_COLOR = "INVALID_COLOR"
    INVALID_LINK = "INVALID_LINK"
    INVALID_DATE = "INVALID_DATE"


PAGES = "business_pages"

__all__ = ["SiteAction", "Section", "ReasonCode", "PAGES"]
