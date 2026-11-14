# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""India: EPF (12% + 12% of basic up to the wage ceiling), ESIC (on gross up to the limit), Professional Tax (a state
slab - Maharashtra by default) and TDS (new regime slabs on the yearly equivalent, after the standard deduction,
with the rebate up to the limit), spread over 12 months."""
from .base import Country, bracket_tax, line


class India(Country):
    code, name, currency = "IN", "India", "INR"
    defaults = {"basic_pct": 50, "pf_pct": 12, "pf_employer_pct": 12, "pf_wage_ceiling": 15000, "esi_pct": 0.75, "esi_employer_pct": 3.25,
                "esi_gross_limit": 21000, "pt_slabs": [[0, 0], [7501, 175], [10001, 200]], "tds_on": True, "tds_standard_deduction": 75000,
                "tds_rebate_upto": 1200000, "tds_cess_pct": 4,
                "tds_slabs": [[0, 0], [400000, 5], [800000, 10], [1200000, 15], [1600000, 20], [2000000, 25], [2400000, 30]]}
    help = {"basic_pct": "Basic pay as % of gross (PF is on basic)", "pf_wage_ceiling": "PF is worked out on basic up to this",
            "esi_gross_limit": "ESI applies when monthly gross is up to this", "pt_slabs": "Professional Tax: [from gross, tax a month]",
            "tds_slabs": "Income tax slabs (new regime): [from yearly income, rate %]", "tds_rebate_upto": "No tax up to this yearly taxable income"}

    def deductions(self, pay: dict, s: dict) -> list[dict]:
        gross, basic = pay["gross"], pay["basic"]
        pf_base = min(basic, s["pf_wage_ceiling"])
        out = [line("pf", "Provident Fund (EPF)", pf_base * s["pf_pct"] / 100), line("pf_er", "Employer PF", pf_base * s["pf_employer_pct"] / 100, True)]
        if pay["monthly_equivalent"] <= s["esi_gross_limit"]:
            out += [line("esi", "ESI", gross * s["esi_pct"] / 100), line("esi_er", "Employer ESI", gross * s["esi_employer_pct"] / 100, True)]
        pt = 0.0
        for start, amount in s["pt_slabs"]:
            pt = amount if gross >= start else pt
        out.append(line("pt", "Professional Tax", pt))
        if s.get("tds_on"):
            taxable = max(0.0, pay["monthly_equivalent"] * 12 - s["tds_standard_deduction"])
            tax = 0.0 if taxable <= s["tds_rebate_upto"] else bracket_tax(taxable, s["tds_slabs"])
            out.append(line("tds", "Income tax (TDS)", tax * (1 + s["tds_cess_pct"] / 100) / 12))
        return [l for l in out if l["amount"] > 0]
