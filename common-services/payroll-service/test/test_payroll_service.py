# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""payroll-service: each country's rules, settings in one place, a month's run from salary / hours / leave, final lock."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import COUNTRIES, clean_change, merged, payslip
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
SALARIED = {"_key": "e1", "name": "Meera", "home_site": "k1", "start_date": "2024-01-01", "pay": {"basis": "monthly", "rate": 30000, "weekly_hours": 48}}
HOURLY = {"_key": "e2", "name": "Imran", "home_site": "k1", "start_date": "2026-11-16", "pay": {"basis": "hourly", "rate": 200, "weekly_hours": 0}}


def test_india_pf_esi_pt_and_unpaid_leave():
    s = merged({"country": "IN"})
    slip = payslip(SALARIED, "2026-11", 0, 3, [{"kind": "bonus", "amount": 1000, "note": "Diwali"}, {"kind": "advance", "amount": 2000}], s)
    assert slip["gross"] == 28000.0                        # 30000 - 3 x 1000 unpaid + 1000 bonus
    got = {l["code"]: l["amount"] for l in slip["deductions"] + slip["employer"]}
    assert got["pf"] == 1620.0 and got["pf_er"] == 1620.0   # 12% of basic 13500 (50% of 27000)
    assert "esi" not in got and got["pt"] == 200 and "tds" not in got     # above the ESI limit; under the tax rebate
    assert slip["net"] == 28000 - 1620 - 200 - 2000 and slip["cost"] == 28000 + 1620


def test_australia_singapore_and_overtime():
    au = payslip({**SALARIED, "pay": {"basis": "monthly", "rate": 6000, "weekly_hours": 38}}, "2026-11", 0, 0, [], merged({"country": "AU"}))
    lines = {l["code"]: l["amount"] for l in au["deductions"] + au["employer"]}
    assert lines["super"] == 720.0 and 1000 < lines["payg"] < 1300
    sg = payslip({**SALARIED, "pay": {"basis": "monthly", "rate": 10000}}, "2026-11", 0, 0, [], merged({"country": "SG"}))
    lines = {l["code"]: l["amount"] for l in sg["deductions"] + sg["employer"]}
    assert lines["cpf"] == 1600.0 and lines["cpf_er"] == 1360.0 and lines["sdl"] == 11.25     # capped at the 8000 ceiling
    hourly = payslip(HOURLY, "2026-11", 60 * 60, 0, [], merged({}))
    assert hourly["gross"] == 12000.0 and hourly["deductions"] == []                           # basic: no statutory lines
    ot = payslip({**HOURLY, "pay": {"basis": "hourly", "rate": 200, "weekly_hours": 40}}, "2026-11", 100 * 60, 0, [], merged({}))
    assert ot["earnings"][-1]["code"] == "overtime"                       # past 40 h a week x 15 of the month's 30 days (86.7 h)
    assert ot["earnings"][-1]["amount"] == round((100 - 40 * 52 / 12 / 2) * 200 * 0.5, 2)
    with pytest.raises(ValueError, match="UNKNOWN_SETTING"):
        clean_change("IN", {"super_pct": 9}, None)
    assert clean_change("IN", {"pf_pct": 10}, None)["rates"] == {"pf_pct": 10} and set(COUNTRIES) == {"", "IN", "AU", "SG"}


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, "payroll_requests", handle, cfg.live_criteria)
    harness.seed("employees", "e1", {**{k: v for k, v in SALARIED.items() if k != "_key"}, "tenant_id": "b1"})
    harness.seed("employees", "e2", {**{k: v for k, v in HOURLY.items() if k != "_key"}, "tenant_id": "b1"})
    harness.seed("employees", "e3", {"tenant_id": "b1", "name": "Gone", "start_date": "2020-01-01", "end_date": "2026-10-31", "pay": {"rate": 1}})
    harness.seed("attendance", "a1", {"tenant_id": "b1", "employee_id": "e2", "date": "2026-11-17", "worked_min": 480})
    harness.seed("leaves", "l1", {"tenant_id": "b1", "employee_id": "e1", "state": "approved", "paid": False, "first": "2026-11-20", "last": "2026-11-23"})
    return harness


def call(h, **f):
    return h.call("payroll_requests", "payroll-service", {"tenant_id": "b1", **f})


def test_a_month_from_settings_to_final(h):
    assert call(h, action="SET_SETTINGS", country="IN", rates={"pt_slabs": [[0, 0]]}).fields["settings"]["changed"] == ["pt_slabs"]
    assert call(h, action="SET_SETTINGS", country="XX").reason == "UNKNOWN_COUNTRY"
    assert call(h, action="ADJUST", month="2026-11", employee_id="e1", kind="bonus", amount=500).ok
    assert call(h, action="ADJUST", month="2026-11", employee_id="e1", kind="gift", amount=5).reason == "INVALID_AMOUNT"
    run = call(h, action="RUN", month="2026-11").fields["run"]
    assert run["people"] == 2 and run["country"] == "IN"                      # e3 left before November
    slips = {s["employee_id"]: s for s in call(h, action="MONTH", month="2026-11").fields["payslips"]}
    assert slips["e1"]["unpaid_days"] == 3 and slips["e1"]["gross"] == 30000 - 3000 + 500   # Sunday 22nd not counted
    assert slips["e2"]["gross"] == 1600.0 and slips["e2"]["worked_hours"] == 8.0
    done = call(h, action="FINALISE", month="2026-11")
    assert done.fields["run"]["final"] and done.fields["cost_by_site"]["k1"] == slips["e1"]["cost"] + slips["e2"]["cost"]
    assert call(h, action="RUN", month="2026-11").reason == "ALREADY_FINAL"
    assert call(h, action="ADJUST", month="2026-11", employee_id="e1", kind="bonus", amount=1).reason == "ALREADY_FINAL"
    assert h.call("payroll_requests", "payroll-service", {"tenant_id": "b2", "action": "MONTH", "month": "2026-11"}).fields["payslips"] == []


def test_payslips_go_out_only_once_locked_and_to_reachable_people(h):
    h.seed("employees", "e1", {**{k: v for k, v in SALARIED.items() if k != "_key"}, "tenant_id": "b1", "email": "meera@x.in", "phone": ""})
    pdf = [{"name": "payslip.pdf", "mime": "application/pdf", "data_b64": "JVBERg==", "url": "https://k/api/v1/files/t/payslip.pdf"}]
    assert call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e1").reason == "NO_RUN"
    call(h, action="RUN", month="2026-11")
    assert call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e1").reason == "MONTH_NOT_FINAL"
    call(h, action="FINALISE", month="2026-11")
    assert call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e2", channels=["email"]).reason == "NO_CONTACT"
    assert call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e1", channels=["fax"]).reason == "INVALID_CHANNEL"
    sent = call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e1", channels=["email", "whatsapp"], attachments=pdf, actor_name="Omar")
    assert sent.ok and sent.fields["payslip"]["sent"][0]["channels"] == ["email"]          # no phone: WhatsApp left out
    queued = h.rows("notifications")
    assert len(queued) == 1 and queued[0]["template"] == "payslip" and queued[0]["attachments"] == pdf
    assert call(h, action="SEND_PAYSLIP", month="2026-11", employee_id="e1").ok                 # sent again: a new message
    assert len(h.rows("notifications")) == 2
    assert h.call("payroll_requests", "payroll-service", {"tenant_id": "b2", "action": "SEND_PAYSLIP", "month": "2026-11",
                                                          "employee_id": "e1"}).reason == "NO_RUN"
