# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Money as whole minor units (cents, paise) with its currency, so sums never drift; currencies are ISO codes.
Every amount keeps its currency: today a fund holds one, and the totals are kept per currency so more can follow."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

DECIMALS = {"JPY": 0, "KRW": 0, "IDR": 0, "VND": 0}      # the rest use 2


def minor(amount, currency: str) -> int:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_AMOUNT")
    places = DECIMALS.get(currency, 2)
    cents = int((value * (10 ** places)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if cents <= 0 or cents > 10 ** 15:
        raise ValueError("INVALID_AMOUNT")
    return cents


def major(cents: int, currency: str) -> float:
    return cents / (10 ** DECIMALS.get(currency, 2))


def currency(code) -> str:
    code = str(code or "").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError("INVALID_CURRENCY")
    return code


def convert(amount: int, frm: str, to: str, rate) -> int:
    """Minor units of `frm` into minor units of `to` at `rate` (units of `to` for one unit of `frm`)."""
    try:
        r = Decimal(str(rate))
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_RATE")
    if r <= 0 or r > 10 ** 9:
        raise ValueError("INVALID_RATE")
    shift = Decimal(10) ** (DECIMALS.get(to, 2) - DECIMALS.get(frm, 2))
    return int((Decimal(amount) * r * shift).quantize(Decimal(1), rounding=ROUND_HALF_UP))
