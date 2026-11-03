# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""LOGIN_EXTERNAL — sign in with a provider (Google): the verified email finds the account (donor, volunteer or admin).
No account yet -> accepted with registered=false plus the verified email and name, so the product can create the person
and then LINK_EXTERNAL. A provider login never grants a role: the role is whatever the account already has."""
from grepx_service import RequestContext

from dto import AuthField as F
from .common import Deps, accept_session, provider_identity


def handle(ctx: RequestContext) -> None:
    identity, problem = provider_identity(ctx)
    if problem:
        return ctx.reject(problem)
    deps = Deps.get()
    cred = deps.repo.by_email(identity.email)
    if cred is None:
        return ctx.accept({F.ID_TOKEN_ENC: "", F.REGISTERED: False, F.EMAIL: identity.email, F.NAME: identity.name})
    if cred.external.get(identity.provider) != identity.subject:
        cred.external[identity.provider] = identity.subject
        deps.repo.save(cred)
    accept_session(ctx, cred)
