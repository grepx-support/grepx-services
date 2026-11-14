# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A business's payroll settings in one place: its country (which statutory rules apply) and every rate - the
country's defaults, with whatever the business changed on top. Only known rates can be changed."""
from __future__ import annotations

from .countries import COUNTRIES

COMMON = {"overtime_multiplier": 1.5, "days_off": [6]}
COMMON_HELP = {"overtime_multiplier": "Overtime hours are paid at this many times the hourly rate",
               "days_off": "Weekly days off (0 = Monday ... 6 = Sunday)"}


def merged(own: dict | None) -> dict:
    own = own or {}
    country = COUNTRIES.get(own.get("country", ""), COUNTRIES[""])
    rates = {**COMMON, **country.defaults, **{k: v for k, v in (own.get("rates") or {}).items() if k in {**COMMON, **country.defaults}}}
    return {"country": country.code, "country_name": country.name, "currency": country.currency, "rates": rates,
            "help": {**COMMON_HELP, **country.help}, "changed": sorted(k for k in (own.get("rates") or {}) if k in rates)}


def clean_change(country: str, rates: dict, current: dict | None) -> dict:
    if country not in COUNTRIES:
        raise ValueError("UNKNOWN_COUNTRY")
    allowed = {**COMMON, **COUNTRIES[country].defaults}
    unknown = set(rates) - set(allowed)
    if unknown:
        raise ValueError("UNKNOWN_SETTING")
    keep = {k: v for k, v in ((current or {}).get("rates") or {}).items() if k in allowed} if (current or {}).get("country") == country else {}
    for k, v in rates.items():
        if v is None:
            keep.pop(k, None)                      # back to the country's default
        elif type(v) is not type(allowed[k]) and not (isinstance(v, (int, float)) and isinstance(allowed[k], (int, float))):
            raise ValueError("UNKNOWN_SETTING")
        else:
            keep[k] = v
    return {"country": country, "rates": keep}
