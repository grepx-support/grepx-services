# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for crm-service vocabulary."""
from enum import Enum

CONTACTS, DEALS, ACTIVITIES, PIPELINES = "crm_contacts", "crm_deals", "crm_activities", "crm_pipelines"


class CrmAction(str, Enum):
    SAVE_CONTACT = "SAVE_CONTACT"        # a person or a company (a person can belong to a company)
    SAVE_DEAL = "SAVE_DEAL"              # a deal: title, contact, value, stage, expected close, owner
    MOVE_DEAL = "MOVE_DEAL"              # to a stage and a place in its column (drag and drop)
    CLOSE_DEAL = "CLOSE_DEAL"            # won, or lost with a reason
    REOPEN_DEAL = "REOPEN_DEAL"
    LOG_ACTIVITY = "LOG_ACTIVITY"        # note, call, email, meeting, WhatsApp, task (with a due date)
    COMPLETE_ACTIVITY = "COMPLETE_ACTIVITY"
    SAVE_PIPELINE = "SAVE_PIPELINE"      # the business's stages (name, win chance, colour, days before a deal goes stale)
    BOARD = "BOARD"                      # the pipeline: stages with their open deals, totals, weighted value, stale flags
    TIMELINE = "TIMELINE"                # one contact: details, people of the company, deals, every activity newest first
    AGENDA = "AGENDA"                    # open tasks: overdue, today, upcoming (one person's or everyone's)
    INSIGHTS = "INSIGHTS"                # forecast by month, win rate, average days to win, by owner, by source, lost reasons


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    INVALID_NAME = "INVALID_NAME"
    INVALID_KIND = "INVALID_KIND"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_DATE = "INVALID_DATE"
    INVALID_STAGE = "INVALID_STAGE"
    INVALID_STAGES = "INVALID_STAGES"
    UNKNOWN_CONTACT = "UNKNOWN_CONTACT"
    UNKNOWN_DEAL = "UNKNOWN_DEAL"
    UNKNOWN_ACTIVITY = "UNKNOWN_ACTIVITY"
    DEAL_CLOSED = "DEAL_CLOSED"
    DEAL_OPEN = "DEAL_OPEN"
    REASON_NEEDED = "REASON_NEEDED"


__all__ = ["CrmAction", "ReasonCode", "CONTACTS", "DEALS", "ACTIVITIES", "PIPELINES"]
