"""REGISTER — create login credentials for a user id (created by the product's people service)."""
from grepx_auth import hash_password
from grepx_service import RequestContext

from domain import MIN_PASSWORD
from dto import AuthField, ReasonCode
from repository import Credential
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    user_id, email = ctx.text(AuthField.USER_ID), ctx.text(AuthField.EMAIL).lower()
    password = deps.box.open(ctx.text(AuthField.PASSWORD_ENC))
    if not user_id or not email or not password:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    if len(password) < MIN_PASSWORD:
        return ctx.reject(ReasonCode.WEAK_PASSWORD)
    existing = deps.repo.by_email(email)
    if existing and existing.user_id != user_id:
        return ctx.reject(ReasonCode.EMAIL_TAKEN)
    deps.repo.save(Credential(user_id, email, hash_password(password), ctx.text(AuthField.TENANT_ID)))
    ctx.accept({AuthField.PASSWORD_ENC: ""})
