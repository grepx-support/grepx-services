# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for signup-service. A sign-up holds its short name while the owner confirms their email (a link) and
mobile (a code); then exactly one caller sets the business up (BEGIN_SETUP) and the short name points to it (ACTIVATE)."""
from datetime import timedelta

from grepx_service import ActionDispatcher, RequestContext, new_key, notify, state_of

import domain as d
from dto import ADDRESSES, SIGNUPS, ReasonCode, SignupAction, SignupStage

SETUP_MINUTES = 10      # a set-up that never finished may be tried again after this long


def _taken(ctx: RequestContext, slug: str, email: str = "", now=None) -> bool:
    """The short name points to a business, or another person's unfinished sign-up holds it."""
    if ctx.read.accepted_one(ADDRESSES, slug) is not None:
        return True
    now = now or d.utcnow()
    return any(d.holds(s, now) and s.get("email") != email for s in ctx.read.accepted(SIGNUPS, slug=slug))


def _save(ctx: RequestContext, row: dict) -> dict:
    ctx.emitter.submit(SIGNUPS, row["signup_id"], "ACCEPTED", row)
    return row


def _public(row: dict) -> dict:
    """What callers may see of a sign-up: never the hashes or the sealed password."""
    keep = ("signup_id", "product", "business_name", "slug", "owner_name", "stage", "email_ok", "phone_ok", "business_id",
            "reason", "created_at", "hold_until", "code_tries", "start_with")
    return {**{k: row.get(k) for k in keep}, "email": d.masked_email(row.get("email", "")), "phone": d.masked_phone(row.get("phone", ""))}


def _send_link(ctx: RequestContext, row: dict, token: str) -> None:
    link = f"{row['link']}{'&' if '?' in row['link'] else '?'}signup={row['signup_id']}&token={token}"
    notify(ctx.emitter, "signup_email", email=row["email"], channels=["email"], auto=False, ref=f"signup-{row['signup_id']}-e{row['email_sends']}",
           values={"name": row["owner_name"], "first_name": row["owner_name"].split(" ")[0], "business": row["business_name"], "link": link})


def _send_code(ctx: RequestContext, row: dict, code: str) -> None:
    notify(ctx.emitter, "signup_code", phone=row["phone"], channels=["sms", "whatsapp"], auto=False,
           ref=f"signup-{row['signup_id']}-p{row['code_sends']}", values={"code": code, "business": row["business_name"]})


def _live(ctx: RequestContext) -> dict | None:
    row = ctx.read.accepted_one(SIGNUPS, ctx.text("signup_id"))
    if row is None:
        ctx.reject(ReasonCode.UNKNOWN_SIGNUP)
        return None
    if row.get("stage") in (SignupStage.ACTIVE.value, SignupStage.FAILED.value, SignupStage.REPLACED.value):
        ctx.reject(ReasonCode.ALREADY_DONE, row.get("stage", ""))
        return None
    if d.at(row.get("hold_until", "")) <= d.utcnow() and row.get("stage") == SignupStage.PENDING.value:
        ctx.reject(ReasonCode.SIGNUP_EXPIRED)
        return None
    return state_of(row)


def _checked(row: dict) -> dict:
    both = row.get("email_ok") and row.get("phone_ok")
    if both and row.get("stage") == SignupStage.PENDING.value:
        row["stage"] = SignupStage.VERIFIED.value
    return row


def check(ctx: RequestContext) -> None:
    slug = ctx.text("slug").lower() or d.suggest_slug(ctx.text("business_name"))
    problem = d.slug_problem(slug)
    if not problem and _taken(ctx, slug, ctx.text("email").lower()):
        problem = ReasonCode.SLUG_TAKEN.value
    ctx.accept({"slug": slug, "available": not problem, "problem": problem})


def start(ctx: RequestContext) -> None:
    try:
        clean = d.clean_signup({k: ctx.get(k) for k in ("business_name", "slug", "owner_name", "email", "phone", "currency", "timezone",
                                                        "product", "password_enc", "website")})
    except ValueError as exc:
        return ctx.reject(str(exc))
    now = d.utcnow()
    if _taken(ctx, clean["slug"], clean["email"], now):
        return ctx.reject(ReasonCode.SLUG_TAKEN)
    for old in ctx.read.accepted(SIGNUPS, email=clean["email"]):        # starting again replaces an unfinished sign-up
        if old.get("stage") in (SignupStage.PENDING.value, SignupStage.VERIFIED.value):
            _save(ctx, {**state_of(old), "stage": SignupStage.REPLACED.value, "password_enc": ""})
    signup_id, token, code = new_key(), d.new_token(), d.new_code()
    row = {"signup_id": signup_id, **clean, "password_enc": ctx.text("password_enc"), "link": ctx.text("link") or "/#/signup/email",
           "ip": ctx.text("ip")[:64], "stage": SignupStage.PENDING.value, "email_ok": False, "phone_ok": False,
           "email_digest": d.digest(token, signup_id), "code_digest": d.digest(code, signup_id), "code_until": d.later(now, minutes=d.CODE_MINUTES),
           "code_tries": 0, "email_sends": 1, "code_sends": 1, "sent_at": d.iso(now), "created_at": d.iso(now),
           "hold_until": d.later(now, hours=d.HOLD_HOURS), "business_id": "", "reason": "",
           "start_with": "empty" if ctx.text("start_with") == "empty" else "demo"}      # a shop full of sample data (default), or empty
    _save(ctx, row)
    _send_link(ctx, row, token)
    _send_code(ctx, row, code)
    ctx.accept({"signup": _public(row)})


def confirm_email(ctx: RequestContext) -> None:
    row = _live(ctx)
    if row is None:
        return None
    if not row.get("email_ok"):
        if d.digest(ctx.text("token"), row["signup_id"]) != row.get("email_digest"):
            return ctx.reject(ReasonCode.WRONG_LINK)
        row = _save(ctx, _checked({**row, "email_ok": True}))
    ctx.accept({"signup": _public(row)})


def confirm_phone(ctx: RequestContext) -> None:
    """A wrong code is counted (accepted with confirmed: false), so the count survives; after MAX_TRIES a new code is needed."""
    row = _live(ctx)
    if row is None:
        return None
    if not row.get("phone_ok"):
        if int(row.get("code_tries") or 0) >= d.MAX_TRIES:
            return ctx.reject(ReasonCode.TOO_MANY_TRIES)
        if d.at(row.get("code_until", "")) <= d.utcnow():
            return ctx.reject(ReasonCode.CODE_EXPIRED)
        if d.digest(ctx.text("code"), row["signup_id"]) != row.get("code_digest"):
            row = _save(ctx, {**row, "code_tries": int(row.get("code_tries") or 0) + 1})
            return ctx.accept({"confirmed": False, "tries_left": d.MAX_TRIES - row["code_tries"], "signup": _public(row)})
        row = _save(ctx, _checked({**row, "phone_ok": True}))
    ctx.accept({"confirmed": True, "signup": _public(row)})


def resend(ctx: RequestContext) -> None:
    row = _live(ctx)
    if row is None:
        return None
    now = d.utcnow()
    if d.at(row.get("sent_at", "")) + timedelta(seconds=d.RESEND_SECONDS) > now:
        return ctx.reject(ReasonCode.TOO_SOON)
    what = ctx.text("what") or "phone"
    if what == "email" and not row.get("email_ok"):
        token = d.new_token()
        row = {**row, "email_digest": d.digest(token, row["signup_id"]), "email_sends": int(row.get("email_sends") or 0) + 1, "sent_at": d.iso(now)}
        _send_link(ctx, _save(ctx, row), token)
    elif what == "phone" and not row.get("phone_ok"):
        code = d.new_code()
        row = {**row, "code_digest": d.digest(code, row["signup_id"]), "code_until": d.later(now, minutes=d.CODE_MINUTES), "code_tries": 0,
               "code_sends": int(row.get("code_sends") or 0) + 1, "sent_at": d.iso(now)}
        _send_code(ctx, _save(ctx, row), code)
    ctx.accept({"signup": _public(row)})


def begin_setup(ctx: RequestContext) -> None:
    """Hands back the details needed to create the business (with the sealed password) to exactly one caller."""
    row = ctx.read.accepted_one(SIGNUPS, ctx.text("signup_id"))
    if row is None:
        return ctx.reject(ReasonCode.UNKNOWN_SIGNUP)
    row, now = state_of(row), d.utcnow()
    stuck = row.get("stage") == SignupStage.SETTING_UP.value and d.at(row.get("setup_at", "")) + timedelta(minutes=SETUP_MINUTES) <= now
    if row.get("stage") != SignupStage.VERIFIED.value and not stuck:
        return ctx.reject(ReasonCode.NOT_VERIFIED, row.get("stage", ""))
    row = _save(ctx, {**row, "stage": SignupStage.SETTING_UP.value, "setup_at": d.iso(now)})
    ctx.accept({"signup": _public(row), "owner": {"name": row["owner_name"], "email": row["email"], "phone": row["phone"]},
                "password_enc": row.get("password_enc", ""), "currency": row.get("currency", ""), "timezone": row.get("timezone", "")})


def activate(ctx: RequestContext) -> None:
    row = ctx.read.accepted_one(SIGNUPS, ctx.text("signup_id"))
    if row is None:
        return ctx.reject(ReasonCode.UNKNOWN_SIGNUP)
    if row.get("stage") != SignupStage.SETTING_UP.value:
        return ctx.reject(ReasonCode.NOT_SETTING_UP, row.get("stage", ""))
    tenant = ctx.text("business_id")
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_BUSINESS)
    now = d.iso(d.utcnow())
    address = ctx.read.accepted_one(ADDRESSES, row["slug"])
    if address is not None and address.get("business_id") != tenant:
        return ctx.reject(ReasonCode.SLUG_TAKEN)
    ctx.emitter.submit(ADDRESSES, row["slug"], "ACCEPTED", {"slug": row["slug"], "business_id": tenant, "product": row.get("product", ""),
                                                            "moved_to": "", "created_at": now})
    row = _save(ctx, {**state_of(row), "stage": SignupStage.ACTIVE.value, "business_id": tenant, "password_enc": "", "activated_at": now})
    ctx.accept({"signup": _public(row)})


def fail(ctx: RequestContext) -> None:
    row = ctx.read.accepted_one(SIGNUPS, ctx.text("signup_id"))
    if row is None:
        return ctx.reject(ReasonCode.UNKNOWN_SIGNUP)
    if row.get("stage") != SignupStage.SETTING_UP.value:
        return ctx.reject(ReasonCode.NOT_SETTING_UP, row.get("stage", ""))
    row = _save(ctx, {**state_of(row), "stage": SignupStage.FAILED.value, "reason": ctx.text("reason")[:120], "password_enc": ""})
    ctx.accept({"signup": _public(row)})


def set_address(ctx: RequestContext) -> None:
    """Give a business a short name (or a new one): the old name keeps pointing to it (moved_to), so old links still work."""
    tenant, slug = ctx.text("business_id"), ctx.text("slug").lower()
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_BUSINESS)
    problem = d.slug_problem(slug)
    if problem:
        return ctx.reject(problem)
    current = ctx.read.accepted_one(ADDRESSES, slug)
    if (current is not None and current.get("business_id") != tenant) or (current is None and _taken(ctx, slug)):
        return ctx.reject(ReasonCode.SLUG_TAKEN)
    now = d.iso(d.utcnow())
    for old in ctx.read.accepted(ADDRESSES):
        if old.get("business_id") == tenant and old["_key"] != slug and not old.get("moved_to"):
            ctx.emitter.submit(ADDRESSES, old["_key"], "ACCEPTED", {**state_of(old), "moved_to": slug})
    row = {"slug": slug, "business_id": tenant, "product": ctx.text("product") or (current or {}).get("product", ""), "moved_to": "",
           "created_at": (current or {}).get("created_at") or now}
    ctx.emitter.submit(ADDRESSES, slug, "ACCEPTED", row)
    ctx.accept({"address": row})


handle = ActionDispatcher({SignupAction.CHECK: check, SignupAction.START: start, SignupAction.CONFIRM_EMAIL: confirm_email,
                           SignupAction.CONFIRM_PHONE: confirm_phone, SignupAction.RESEND: resend, SignupAction.BEGIN_SETUP: begin_setup,
                           SignupAction.ACTIVATE: activate, SignupAction.FAIL: fail, SignupAction.SET_ADDRESS: set_address},
                          SignupAction, "signup_requests")
