# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for fund-service: one module per concern."""
from grepx_service import ActionDispatcher

from dto import FundAction
from . import plan, record, save, views

TABLE = "fund_requests"
ROUTES = {
    FundAction.SAVE_FUND: save.fund,
    FundAction.SAVE_PARTY: save.party,
    FundAction.RECORD: record.handle,
    FundAction.REVERSE: record.reverse,
    FundAction.OVERVIEW: views.overview,
    FundAction.FUND: views.fund,
    FundAction.SET_PLAN: plan.handle,
}
handle = ActionDispatcher(ROUTES, FundAction, TABLE)
