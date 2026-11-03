"""Person rows: load, unique email, save, and the product's profile plugin (config plugins.profile)."""
from __future__ import annotations

from typing import Optional

from grepx_service import RequestContext, state_of
from grepx_service.plugins import plugin

from domain import ProfileError, clean_contact
from dto import CONTACT_FIELDS, PEOPLE_TABLE, PersonField as F


def load(ctx: RequestContext, person_id: str) -> Optional[dict]:
    return state_of(ctx.read.accepted_one(PEOPLE_TABLE, person_id))


def email_owner(ctx: RequestContext, email: str) -> Optional[str]:
    rows = ctx.read.accepted(PEOPLE_TABLE, email=email)
    return rows[0]["_key"] if rows else None


def clean(ctx: RequestContext, raw: dict, partial: bool) -> dict:
    """Contact fields, plus the product's own fields when a profile plugin is configured.
    Plugin interface:  FIELDS = (...);  clean(raw, partial) -> dict   (raises ValueError(<REASON_CODE>))."""
    product = plugin(ctx.cfg, "profile")
    contact = clean_contact({f.value: raw[f.value] for f in CONTACT_FIELDS if f.value in raw}, partial=partial)
    if product is None:
        return contact
    try:
        extra = product.clean({k: raw[k] for k in product.FIELDS if k in raw}, partial)
    except ValueError as exc:
        raise ProfileError(str(exc)) from exc
    return {**contact, **extra}


def editable(ctx: RequestContext) -> tuple:
    product = plugin(ctx.cfg, "profile")
    return tuple(f.value for f in CONTACT_FIELDS) + tuple(getattr(product, "FIELDS", ()) if product else ())


def save(ctx: RequestContext, person: dict) -> None:
    ctx.emitter.submit(PEOPLE_TABLE, person[F.PERSON_ID.value], "ACCEPTED", person)
    ctx.accept({F.PERSON_ID: person[F.PERSON_ID.value], F.REF_CODE: person.get(F.REF_CODE.value, "")})
