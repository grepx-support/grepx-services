# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What a fund is expected to earn, and whether it does. A plan says, for each use of the money (an outlet, a
project), the EBITDA it is expected to make a month, when it starts and how many months it takes to get there (a
straight ramp). From the plan: the month-by-month EBITDA over the horizon, what is paid out to the parties (a share
of EBITDA), payback month, ROI, NPV at the discount rate and IRR. Actual EBITDA per use (given by the product, e.g.
the outlet's sales less its costs) is set against the plan."""
from __future__ import annotations


def clean_plan(raw: dict) -> dict:
    def n(v, low=0.0, high=1e15):
        try:
            x = float(v or 0)
        except (TypeError, ValueError):
            raise ValueError("INVALID_AMOUNT")
        if not low <= x <= high:
            raise ValueError("INVALID_AMOUNT")
        return x
    uses = [{"purpose": " ".join(str(u.get("purpose") or "").split())[:80], "monthly_ebitda": n(u.get("monthly_ebitda")),
             "starts_in": int(n(u.get("starts_in"), 0, 120)), "ramp": int(n(u.get("ramp"), 0, 60))} for u in raw.get("uses") or [] if u.get("purpose")]
    return {"horizon": int(n(raw.get("horizon") or 36, 6, 240)), "discount_pct": n(raw.get("discount_pct") or 12, 0, 100),
            "payout_pct": n(raw.get("payout_pct") or 50, 0, 100), "hurdle_pct": n(raw.get("hurdle_pct") or 0, 0, 100), "uses": uses}


def ebitda_curve(plan: dict) -> list[float]:
    out = [0.0] * plan["horizon"]
    for u in plan["uses"]:
        for m in range(plan["horizon"]):
            since = m - u["starts_in"]
            if since < 0:
                continue
            out[m] += u["monthly_ebitda"] * (min(1.0, (since + 1) / u["ramp"]) if u["ramp"] else 1.0)
    return out


def irr(flows: list[float]) -> float | None:
    """Monthly flows (first negative) -> yearly internal rate of return %, by bisection; None when it never pays back."""
    if not flows or flows[0] >= 0 or sum(flows) <= 0:
        return None
    lo, hi = -0.99, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        npv = sum(f / (1 + mid) ** i for i, f in enumerate(flows))
        lo, hi = (mid, hi) if npv > 0 else (lo, mid)
    return round(((1 + lo) ** 12 - 1) * 100, 2)


def project(plan: dict, invested: int) -> dict:
    """invested: minor units put in (capital received). Returns the plan's numbers, all in minor units."""
    curve = [round(x * 100) for x in ebitda_curve(plan)]           # plan amounts are major units
    paid = [round(x * plan["payout_pct"] / 100) for x in curve]
    cumulative, run, payback = [], -invested, None
    for m, x in enumerate(paid):
        run += x
        cumulative.append(run)
        if payback is None and run >= 0:
            payback = m + 1
    rate = (1 + plan["discount_pct"] / 100) ** (1 / 12) - 1
    npv = round(-invested + sum(x / (1 + rate) ** (i + 1) for i, x in enumerate(paid)))
    total = sum(paid)
    return {"months": [{"month": i + 1, "ebitda": e, "paid_out": p, "cumulative": c} for i, (e, p, c) in enumerate(zip(curve, paid, cumulative))],
            "expected_ebitda_month": curve[-1] if curve else 0, "expected_ebitda_year": sum(curve[-12:]), "paid_out": total,
            "payback_month": payback, "roi_pct": round((total - invested) / invested * 100, 1) if invested else None, "npv": npv,
            "irr_pct": irr([-invested] + paid) if invested else None, "multiple": round(total / invested, 2) if invested else None}


def against_plan(plan: dict, actual: dict[str, list[float]]) -> list[dict]:
    """Per use: planned EBITDA a month against the actual average of the months given (major units)."""
    out = []
    for u in plan["uses"]:
        months = actual.get(u["purpose"]) or []
        avg = sum(months) / len(months) if months else None
        out.append({"purpose": u["purpose"], "planned": u["monthly_ebitda"], "actual": round(avg, 2) if avg is not None else None,
                    "months": len(months), "pct_of_plan": round(avg / u["monthly_ebitda"] * 100, 1) if avg is not None and u["monthly_ebitda"] else None})
    return out
