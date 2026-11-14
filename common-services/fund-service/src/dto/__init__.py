# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for fund-service vocabulary."""
from enum import Enum

FUNDS, PARTIES, ENTRIES = "funds", "fund_parties", "fund_entries"


class FundAction(str, Enum):
    SAVE_FUND = "SAVE_FUND"      # a fund: name, kind, currency, target, loan rate
    SAVE_PARTY = "SAVE_PARTY"    # an investor, partner, lender or grant giver
    RECORD = "RECORD"            # one movement: promise, money in, put to use, paid back, interest, cost
    REVERSE = "REVERSE"          # take an entry back (it stays, marked reversed - the history is never rewritten)
    OVERVIEW = "OVERVIEW"        # every fund with its totals, overdue promises, the business's totals per currency
    FUND = "FUND"                # one fund: totals, parties and shares, uses, utilisation, plan, projection, actual vs plan
    STATEMENT = "STATEMENT"      # one party's statement: per fund promised, in, back, share; their movements in a period
    SEND_STATEMENT = "SEND_STATEMENT"  # email / WhatsApp the statement (the PDF the caller made attached); each send kept
    SET_PLAN = "SET_PLAN"        # the fund's plan: expected EBITDA per use, start, ramp; horizon, discount, payout


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    UNKNOWN_FUND = "UNKNOWN_FUND"
    UNKNOWN_PARTY = "UNKNOWN_PARTY"
    UNKNOWN_ENTRY = "UNKNOWN_ENTRY"
    INVALID_NAME = "INVALID_NAME"
    INVALID_KIND = "INVALID_KIND"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_DATE = "INVALID_DATE"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"    # a fund's currency can't change once money moved
    RATE_NEEDED = "RATE_NEEDED"                # money in another currency needs its exchange rate
    INVALID_RATE = "INVALID_RATE"
    NO_CONTACT = "NO_CONTACT"
    NOT_ENOUGH_AVAILABLE = "NOT_ENOUGH_AVAILABLE"
    ALREADY_REVERSED = "ALREADY_REVERSED"


__all__ = ["FundAction", "ReasonCode", "FUNDS", "PARTIES", "ENTRIES"]
