"""CREATE — register a person (sign-up, walk-in, kiosk or import). Welcomes them and records who invited them."""
import secrets

from grepx_service import RequestContext, notify, now_iso
from grepx_service.plugins import template_for

from domain import ProfileError, placeholder_email
from dto import PEOPLE_TABLE, PersonField as F, ReasonCode
from .common import clean, email_owner, save


def handle(ctx: RequestContext) -> None:
    raw = dict(ctx.fields)
    if not raw.get("email") and ctx.get(F.ALLOW_NO_EMAIL, False):
        raw["email"] = placeholder_email()
    try:
        profile = clean(ctx, raw, partial=False)
    except ProfileError as exc:
        return ctx.reject(str(exc))
    if email_owner(ctx, profile["email"]):
        return ctx.reject(ReasonCode.EMAIL_TAKEN)
    referrer = ctx.read.accepted(PEOPLE_TABLE, ref_code=ctx.text(F.INVITE_CODE)) if ctx.text(F.INVITE_CODE) else []
    person = {**profile, F.PERSON_ID.value: ctx.text(F.PERSON_ID) or ctx.key, F.REF_CODE.value: secrets.token_hex(3),
              F.CAL_TOKEN.value: secrets.token_urlsafe(16), F.REFERRED_BY.value: referrer[0]["_key"] if referrer else "",
              F.SOURCE.value: ctx.text(F.SOURCE) or "online", F.TENANT_ID.value: ctx.text(F.TENANT_ID), F.CREATED.value: now_iso(),
              F.PHOTO_ID.value: ""}
    save(ctx, person)
    if person[F.SOURCE.value] == "online":
        notify(ctx.emitter, template_for(ctx.cfg, "welcome"), email=person["email"], phone=person["phone"],
               ref=f"welcome-{person['person_id']}",
               values={"first_name": person["name"].split()[0], "name": person["name"], "link": ctx.text(F.LINK)},
               tenant_id=person[F.TENANT_ID.value], user_id=person["person_id"])
