"""SET_PASSWORD — an admin sets a typed password, or a generated one returned sealed (shown once)."""
import secrets

from grepx_auth import hash_password
from grepx_service import RequestContext

from domain import MIN_PASSWORD
from dto import AuthField, ReasonCode
from repository import Credential
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    user_id = ctx.text(AuthField.USER_ID)
    cred = deps.repo.by_id(user_id)
    if cred is None:
        email = ctx.text(AuthField.EMAIL)
        if not email:
            return ctx.reject(ReasonCode.UNKNOWN_USER)
        cred = Credential(user_id, email, "", ctx.text(AuthField.TENANT_ID))
    password = deps.box.open(ctx.text(AuthField.PASSWORD_ENC)) or secrets.token_urlsafe(9)
    if len(password) < MIN_PASSWORD:
        return ctx.reject(ReasonCode.WEAK_PASSWORD)
    cred.password_hash = hash_password(password)
    deps.repo.save(cred)
    ctx.accept({AuthField.PASSWORD_ENC: "", AuthField.TEMP_PASSWORD_ENC: deps.box.seal(password)})
