# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""signup-service: details held, email link + phone code confirmed, one set-up, the short name points to the business."""
from datetime import timedelta
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

import domain as d
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
S = "signup-service"
ME = {"business_name": "Galaxy Mobiles & Laptops", "owner_name": "Ravi Kumar", "email": "Ravi@Galaxy.test", "phone": "+91 98450 12345",
      "password_enc": "sealed-pw", "product": "shop", "currency": "inr", "timezone": "Asia/Kolkata", "link": "http://h:1/#/signup/email"}


def harness():
    return ServiceHarness().add(cfg, "signup_requests", handle, cfg.live_criteria)


def call(h, action, **fields):
    return h.call("signup_requests", S, {"action": action, **fields})


def sent(h, template):
    """The latest message of this template and what it carried (the code / the link)."""
    rows = [r for r in h.rows("notifications") if r.get("template") == template]
    return rows[-1]


def test_rules():
    assert d.suggest_slug("Galaxy Mobiles & Laptops") == "galaxy-mobiles-and-laptops"
    assert d.slug_problem("galaxy") == "" and d.slug_problem("ab") == "INVALID_SLUG" and d.slug_problem("admin") == "RESERVED_SLUG"
    assert d.slug_problem("-x-y") == "INVALID_SLUG" and d.slug_problem("a--b") == "INVALID_SLUG" and d.slug_problem("Big") == "INVALID_SLUG"
    assert d.clean_phone("+91 98450-12345") == "+919845012345" and d.clean_phone("123") == ""
    clean = d.clean_signup({**ME, "slug": ""})
    assert (clean["slug"], clean["email"], clean["phone"], clean["currency"]) == ("galaxy-mobiles-and-laptops", "ravi@galaxy.test", "+919845012345", "INR")
    for bad, reason in (({"website": "x"}, "SPAM"), ({"business_name": "G"}, "INVALID_BUSINESS_NAME"), ({"email": "no"}, "INVALID_EMAIL"),
                        ({"phone": "12"}, "INVALID_PHONE"), ({"slug": "www"}, "RESERVED_SLUG"), ({"password_enc": ""}, "MISSING_PASSWORD")):
        with pytest.raises(ValueError, match=reason):
            d.clean_signup({**ME, **bad})
    assert d.masked_phone("+919845012345") == "+91*******345" and d.masked_email("ravi@galaxy.test") == "ra**@galaxy.test"


def test_sign_up_confirm_set_up_and_address():
    h = harness()
    c = call(h, "CHECK", business_name="Galaxy").fields
    assert (c["slug"], c["available"], c["problem"]) == ("galaxy", True, "")
    v = call(h, "START", **ME, slug="galaxy")
    assert v.ok, v.fields
    signup = v.fields["signup"]
    sid = signup["signup_id"]
    assert (signup["stage"], signup["email"], signup["phone"]) == ("pending", "ra**@galaxy.test", "+91*******345")
    assert "password_enc" not in signup and "code_digest" not in signup
    assert signup["start_with"] == "demo"                                         # sample data unless asked for an empty shop
    row = h.rows("signups")[0]
    assert row["password_enc"] == "sealed-pw" and len(row["code_digest"]) == 64

    link, code = sent(h, "signup_email")["values"]["link"], sent(h, "signup_code")["values"]["code"]
    assert link.startswith("http://h:1/#/signup/email?signup=") and sent(h, "signup_code")["recipient"] == "+919845012345"
    assert {r["channel"] for r in h.rows("notifications") if r["template"] == "signup_code"} == {"sms", "whatsapp"}
    token = link.split("token=")[1]

    # the name is held for this sign-up; another person cannot take it, the same email may start again
    assert call(h, "CHECK", slug="galaxy").fields["problem"] == "SLUG_TAKEN"
    assert call(h, "START", **{**ME, "email": "x@y.test"}, slug="galaxy").reason == "SLUG_TAKEN"

    assert call(h, "BEGIN_SETUP", signup_id=sid).reason == "NOT_VERIFIED"
    assert call(h, "CONFIRM_EMAIL", signup_id=sid, token="nope").reason == "WRONG_LINK"
    assert call(h, "CONFIRM_EMAIL", signup_id=sid, token=token).fields["signup"]["email_ok"] is True
    wrong = call(h, "CONFIRM_PHONE", signup_id=sid, code="000000" if code != "000000" else "111111")
    assert (wrong.fields["confirmed"], wrong.fields["tries_left"]) == (False, 4)
    done = call(h, "CONFIRM_PHONE", signup_id=sid, code=code)
    assert done.fields["confirmed"] and done.fields["signup"]["stage"] == "verified"

    setup = call(h, "BEGIN_SETUP", signup_id=sid)
    assert setup.ok and setup.fields["password_enc"] == "sealed-pw" and setup.fields["owner"]["email"] == "ravi@galaxy.test"
    assert call(h, "BEGIN_SETUP", signup_id=sid).reason == "NOT_VERIFIED"         # only one caller sets the business up
    active = call(h, "ACTIVATE", signup_id=sid, business_id="biz1")
    assert active.fields["signup"]["stage"] == "active" and active.fields["signup"]["business_id"] == "biz1"
    assert h.rows("signups")[0]["password_enc"] == ""                              # the password is not kept after set-up
    assert h.rows("addresses")[0]["business_id"] == "biz1"
    assert call(h, "CHECK", slug="galaxy").fields["problem"] == "SLUG_TAKEN"

    # the operator renames it: the old name keeps pointing to the new one
    assert call(h, "SET_ADDRESS", business_id="biz1", slug="galaxy-mobiles").ok
    rows = {r["_key"]: r for r in h.rows("addresses")}
    assert rows["galaxy"]["moved_to"] == "galaxy-mobiles" and rows["galaxy-mobiles"]["business_id"] == "biz1"
    assert call(h, "SET_ADDRESS", business_id="other", slug="galaxy-mobiles").reason == "SLUG_TAKEN"


def test_codes_expire_tries_run_out_and_resend_waits(monkeypatch):
    h = harness()
    sid = call(h, "START", **ME, slug="tries").fields["signup"]["signup_id"]
    for _ in range(d.MAX_TRIES):
        call(h, "CONFIRM_PHONE", signup_id=sid, code="bad")
    assert call(h, "CONFIRM_PHONE", signup_id=sid, code="bad").reason == "TOO_MANY_TRIES"
    assert call(h, "RESEND", signup_id=sid, what="phone").reason == "TOO_SOON"
    now = d.utcnow()
    monkeypatch.setattr(d, "utcnow", lambda: now + timedelta(seconds=d.RESEND_SECONDS + 1))
    assert call(h, "RESEND", signup_id=sid, what="phone").fields["signup"]["code_tries"] == 0
    code = sent(h, "signup_code")["values"]["code"]
    monkeypatch.setattr(d, "utcnow", lambda: now + timedelta(minutes=d.CODE_MINUTES + 2))
    assert call(h, "CONFIRM_PHONE", signup_id=sid, code=code).reason == "CODE_EXPIRED"
    monkeypatch.setattr(d, "utcnow", lambda: now + timedelta(hours=d.HOLD_HOURS + 1))
    assert call(h, "CONFIRM_EMAIL", signup_id=sid, token="x").reason == "SIGNUP_EXPIRED"
    assert call(h, "CHECK", slug="tries").fields["available"] is True                 # an abandoned sign-up frees its name


def test_an_empty_shop_when_asked():
    h = harness()
    assert call(h, "START", **ME, slug="plain", start_with="empty").fields["signup"]["start_with"] == "empty"
    assert call(h, "START", **{**ME, "email": "x@y.test"}, slug="plain2", start_with="nonsense").fields["signup"]["start_with"] == "demo"


def test_starting_again_replaces_and_failure_frees_the_name():
    h = harness()
    first = call(h, "START", **ME, slug="again").fields["signup"]["signup_id"]
    second = call(h, "START", **ME, slug="again").fields["signup"]["signup_id"]
    stages = {r["_key"]: r["stage"] for r in h.rows("signups")}
    assert (stages[first], stages[second]) == ("replaced", "pending")
    assert call(h, "CONFIRM_EMAIL", signup_id=first, token="x").reason == "ALREADY_DONE"
    row = [r for r in h.rows("signups") if r["_key"] == second][0]
    h2 = [r for r in h.rows("notifications") if r["template"] == "signup_email"][-1]["values"]["link"].split("token=")[1]
    call(h, "CONFIRM_EMAIL", signup_id=second, token=h2)
    code = sent(h, "signup_code")["values"]["code"]
    call(h, "CONFIRM_PHONE", signup_id=second, code=code)
    assert call(h, "BEGIN_SETUP", signup_id=second).ok and row["stage"] == "pending"
    assert call(h, "FAIL", signup_id=second, reason="EMAIL_IN_USE").fields["signup"]["stage"] == "failed"
    assert call(h, "CHECK", slug="again", email="someone@else.test").fields["available"] is True
