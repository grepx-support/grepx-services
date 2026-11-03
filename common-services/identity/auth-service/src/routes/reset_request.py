"""RESET_REQUEST — email a one-time, one-hour reset link. Always ACCEPTED (no account probing)."""
import time

from grepx_service import RequestContext, notify

from domain import RESET_COOLDOWN_SECONDS, RESET_HOURS, fingerprint
from dto import AuthField
from .common import Deps


def handle(ctx: RequestContext) -> None:
    deps = Deps.get()
    cred = deps.repo.by_email(ctx.text(AuthField.EMAIL))
    if cred and time.time() - cred.reset_requested_at >= RESET_COOLDOWN_SECONDS:
        token = deps.tokens.issue({"sub": cred.user_id, "fp": fingerprint(cred.password_hash)}, hours=RESET_HOURS, kind="reset")
        cred.reset_requested_at = time.time()
        deps.repo.save(cred)
        link = f"{ctx.text(AuthField.LINK_BASE).rstrip('/')}/{token}"
        notify(ctx.emitter, "password_reset", email=cred.email, channels=["email"], values={"link": link},
               ref=f"reset-{ctx.key}", tenant_id=cred.tenant_id, user_id=cred.user_id, auto=False)
    ctx.accept()
