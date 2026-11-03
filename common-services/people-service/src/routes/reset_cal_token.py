"""RESET_CAL_TOKEN — new private calendar-feed address; the old one stops working."""
import secrets

from grepx_service import RequestContext

from dto import PersonField as F, ReasonCode
from .common import load, save


def handle(ctx: RequestContext) -> None:
    person = load(ctx, ctx.text(F.PERSON_ID))
    if person is None:
        return ctx.reject(ReasonCode.UNKNOWN_PERSON)
    save(ctx, {**person, F.CAL_TOKEN.value: secrets.token_urlsafe(16)})
