# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for crm-service."""
from grepx_service import ActionDispatcher

from dto import CrmAction as A
from . import activities, contacts, deals, views

ROUTES = {
    A.SAVE_CONTACT: contacts.handle,
    A.SAVE_DEAL: deals.save_deal, A.MOVE_DEAL: deals.move_deal, A.CLOSE_DEAL: deals.close_deal, A.REOPEN_DEAL: deals.reopen_deal,
    A.LOG_ACTIVITY: activities.log, A.COMPLETE_ACTIVITY: activities.complete,
    A.SAVE_PIPELINE: views.save_pipeline, A.BOARD: views.board_view, A.TIMELINE: views.timeline, A.AGENDA: views.agenda, A.INSIGHTS: views.insights_view,
}
handle = ActionDispatcher(ROUTES, A, "crm_requests")
