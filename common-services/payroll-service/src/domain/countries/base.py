# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""One country's payroll rules (Strategy + Template Method): its rates live in settings (defaults here, the business
may change any of them in one place); deductions() turns a month's pay into statutory lines. Each line says whether
the employee pays it (taken from pay) or the employer does (a cost on top)."""
from __future__ import annotations


def line(code: str, label: str, amount: float, employer: bool = False) -> dict:
    return {"code": code, "label": label, "amount": round(max(0.0, amount), 2), "employer": employer}


class Country:
    code, name, currency = "", "Basic (no statutory deductions)", ""
    defaults: dict = {}           # every rate this country uses, with its default value
    help: dict = {}               # what each rate means, shown beside it on the settings page

    def deductions(self, pay: dict, s: dict) -> list[dict]:
        """pay: {gross, basic, monthly_equivalent}. s: this country's rates (defaults + the business's own)."""
        return []


def bracket_tax(yearly: float, brackets: list[list[float]]) -> float:
    """Tax on a yearly income with marginal brackets [[from, rate %], ...] sorted by from."""
    tax = 0.0
    for i, (start, rate) in enumerate(brackets):
        end = brackets[i + 1][0] if i + 1 < len(brackets) else float("inf")
        if yearly > start:
            tax += (min(yearly, end) - start) * rate / 100
    return tax
