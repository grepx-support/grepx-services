"""LINK_EXTERNAL — after the product created the person, attach the provider login to it (no password needed).
The provider token is verified again, so only the owner of that email can link it."""
from grepx_service import RequestContext

from dto import AuthField as F, ReasonCode
from repository import Credential
from .common import Deps, accept_session, provider_identity


def handle(ctx: RequestContext) -> None:
    user_id = ctx.text(F.USER_ID)
    if not user_id:
        return ctx.reject(ReasonCode.MISSING_FIELD)
    identity, problem = provider_identity(ctx)
    if problem:
        return ctx.reject(problem)
    deps = Deps.get()
    cred = deps.repo.by_id(user_id) or Credential(user_id, identity.email, "", ctx.text(F.TENANT_ID))
    if cred.email != identity.email:
        return ctx.reject(ReasonCode.INVALID_TOKEN, detail="the provider email differs from the account email")
    cred.external[identity.provider] = identity.subject
    deps.repo.save(cred)
    accept_session(ctx, cred)
