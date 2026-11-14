# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Australia: PAYG withholding (resident tax brackets on the yearly equivalent, plus the Medicare levy, spread over
12 months) and superannuation guarantee paid by the employer on ordinary time earnings."""
from .base import Country, bracket_tax, line


class Australia(Country):
    code, name, currency = "AU", "Australia", "AUD"
    defaults = {"basic_pct": 100, "super_pct": 12, "medicare_pct": 2, "tax_free_threshold": True,
                "payg_brackets": [[0, 0], [18200, 16], [45000, 30], [135000, 37], [190000, 45]]}
    help = {"super_pct": "Superannuation guarantee %, paid by the employer", "payg_brackets": "Resident tax: [from yearly income, rate %]",
            "tax_free_threshold": "The employee claims the tax-free threshold"}

    def deductions(self, pay: dict, s: dict) -> list[dict]:
        yearly = pay["monthly_equivalent"] * 12
        brackets = s["payg_brackets"] if s.get("tax_free_threshold", True) else [[0, s["payg_brackets"][1][1]], *s["payg_brackets"][2:]]
        tax = bracket_tax(yearly, brackets) + (yearly * s["medicare_pct"] / 100 if yearly > 18200 else 0)
        return [l for l in (line("payg", "PAYG withholding", tax / 12), line("super", "Superannuation", pay["basic"] * s["super_pct"] / 100, True))
                if l["amount"] > 0]
