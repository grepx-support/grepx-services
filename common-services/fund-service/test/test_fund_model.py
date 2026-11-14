# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""fund-service: real spending per use, forecast and runway, suggestions, balance sheet detail, several currencies,
investor statements."""
from domain import convert, forecast, linked, suggestions
from test_fund_service import call, h  # noqa: F401  (h is the shared fixture)

SPEND = {"Outlet A": [{"month": "2026-01", "category": "Ingredients", "amount": 300000}, {"month": "2026-02", "category": "Labour", "amount": 500000},
                      {"month": "2026-03", "category": "Ingredients", "amount": 400000}, {"month": "2025-12", "category": "Rent", "amount": 999}]}


def test_spending_forecast_and_rules():
    entries = [{"kind": "allocate", "purpose": "Outlet A", "amount": 1000000, "date": "2026-01-03", "fund_id": "f"}]
    u = linked([{"purpose": "Outlet A", "amount": 1000000}], entries, SPEND)[0]
    assert (u["spent"], u["left"], u["burn"], u["over"], u["categories"][0]["category"]) == (1200000, -200000, 400000, True, "Ingredients")
    assert convert(10000, "USD", "SGD", "1.35") == 13500 and convert(10000, "SGD", "JPY", "110") == 11000          # 100.00 SGD = 11,000 yen
    f = forecast(1000000, [{"due": "2026-05-10", "missing": 500000, "overdue": False}, {"due": "2026-01-01", "missing": 300000, "overdue": True}],
                 300000, [{"owed": 1200000, "rate_pct": 12}], [], "2026-04")
    exp, worst = f["cases"]["expected"]["months"], f["cases"]["worst"]["months"]
    assert f["interest"] == 12000 and exp[0]["in"] == 300000 and exp[1]["in"] == 500000            # overdue counted now, May's in May
    assert worst[0]["in"] == 0 and worst[2]["in"] == 500000 and f["runway"]["worst"] < f["runway"]["expected"]
    tips = suggestions({"overdue": [{"name": "Asha", "due": "2026-01-01", "missing": 300000, "party_id": "p"}], "forecast": f, "pending": 800000,
                        "available": 1000000, "linked": [u], "loans": [{"fund_id": "l", "name": "Bank", "rate_pct": 12, "owed": 1200000}],
                        "against_plan": [{"purpose": "Outlet A", "pct_of_plan": 60}], "received_long_ago": True})
    assert [t["code"] for t in tips] == ["CHASE_PROMISE", "RUNWAY_SHORT", "USE_OVERSPENT", "BEHIND_PLAN", "REPAY_LOAN"]


def test_currencies_statement_and_balance_detail(h):
    fid = call(h, action="SAVE_FUND", name="Seed round", kind="equity", currency="SGD").fields["fund"]["fund_id"]
    usd = call(h, action="SAVE_FUND", name="US note", kind="loan", currency="USD", rate_pct=10, rate_to_base="1.35").fields["fund"]["fund_id"]
    asha = call(h, action="SAVE_PARTY", name="Asha Capital", email="asha@cap.test").fields["party"]["party_id"]
    rec = lambda **f: call(h, action="RECORD", fund_id=fid, **f)  # noqa: E731
    assert rec(kind="receive", party_id=asha, amount=1000, currency="USD", rate="0").reason == "INVALID_RATE"
    got = rec(kind="receive", party_id=asha, amount=1000, currency="USD", rate="1.35", date="2026-01-10").fields["entry"]
    assert (got["amount"], got["currency"], got["original"]) == (135000, "SGD", {"amount": 100000, "currency": "USD", "rate": "1.35"})
    rec(kind="commit", party_id=asha, amount=5000, date="2026-01-10", due="2026-02-01")
    rec(kind="allocate", amount=1000, purpose="Outlet A", date="2026-01-15")
    call(h, action="RECORD", fund_id=usd, kind="receive", party_id=asha, amount=2000, date="2026-01-12")
    o = call(h, action="OVERVIEW", base="SGD", today="2026-03-01", spending=SPEND).fields
    assert o["in_base"]["received"] == 135000 + 270000 and o["in_base"]["unconverted"] == []
    assert o["position"]["linked"][0]["spent"] == 1200000 and o["position"]["promises"][0]["overdue"]
    assert {t["code"] for t in o["position"]["suggestions"]} >= {"CHASE_PROMISE", "USE_OVERSPENT"}
    sheet = o["balance_sheet"]["SGD"]
    assert sheet["balances"] and sheet["equity"][0]["rows"] == [{"label": "Asha Capital", "amount": 135000}]
    assert call(h, action="OVERVIEW", as_of="2026-01-11").fields["balance_sheet"]["SGD"]["assets_total"] == 135000
    st = call(h, action="STATEMENT", party_id=asha, today="2026-03-01").fields["statement"]
    assert [f["name"] for f in st["funds"]] == ["Seed round", "US note"] and st["funds"][0]["lines"][0]["original"]["currency"] == "USD"
    pdf = [{"name": "statement.pdf", "mime": "application/pdf", "data_b64": "JVBERg=="}]
    sent = call(h, action="SEND_STATEMENT", party_id=asha, attachments=pdf, org="HFT").fields["party"]
    assert sent["statements_sent"][0]["channels"] == ["email"] and h.rows("notifications")[0]["attachments"] == pdf
    nobody = call(h, action="SAVE_PARTY", name="Silent Partner").fields["party"]["party_id"]
    assert call(h, action="SEND_STATEMENT", party_id=nobody).reason == "NO_CONTACT"
