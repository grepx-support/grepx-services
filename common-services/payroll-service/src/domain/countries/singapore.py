# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Singapore: CPF for citizens and permanent residents (employee and employer shares on ordinary wages up to the
monthly ceiling; age bands as settings) and the Skills Development Levy paid by the employer."""
from .base import Country, line


class Singapore(Country):
    code, name, currency = "SG", "Singapore", "SGD"
    defaults = {"basic_pct": 100, "cpf_pct": 20, "cpf_employer_pct": 17, "cpf_wage_ceiling": 8000, "cpf_min_wage": 750,
                "sdl_pct": 0.25, "sdl_min": 2, "sdl_max": 11.25}
    help = {"cpf_wage_ceiling": "CPF is worked out on ordinary wages up to this a month", "cpf_min_wage": "No employee CPF below this wage",
            "sdl_pct": "Skills Development Levy % (employer)"}

    def deductions(self, pay: dict, s: dict) -> list[dict]:
        if pay.get("local", True) is False:
            return [line("sdl", "Skills Development Levy", self.sdl(pay["gross"], s), True)]
        ow = min(pay["gross"], s["cpf_wage_ceiling"])
        employee = ow * s["cpf_pct"] / 100 if pay["gross"] >= s["cpf_min_wage"] else 0
        return [l for l in (line("cpf", "CPF (employee)", employee), line("cpf_er", "CPF (employer)", ow * s["cpf_employer_pct"] / 100, True),
                            line("sdl", "Skills Development Levy", self.sdl(pay["gross"], s), True)) if l["amount"] > 0]

    @staticmethod
    def sdl(gross: float, s: dict) -> float:
        return min(max(gross * s["sdl_pct"] / 100, s["sdl_min"]), s["sdl_max"])
