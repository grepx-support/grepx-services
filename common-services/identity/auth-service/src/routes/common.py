# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Collaborators shared by auth routes (built once, swappable in tests)."""
from __future__ import annotations
import grepx_contracts as gc

import os

from grepx_auth import SecretBox, TokenService, open_settings
from grepx_common import Roles
from grepx_store import database_url, open_store
from grepx_config import load_config

from domain import session_hours
from providers import PROVIDERS, IdentityError
from repository import CredentialRepository

ACCESS_TABLE = gc.access.USER_ACCESS


class Deps:
    repo: CredentialRepository | None = None
    tokens: TokenService | None = None
    box: SecretBox | None = None

    @classmethod
    def get(cls) -> "Deps":
        if cls.repo is None:
            from pathlib import Path
            cfg = load_config(Path(__file__).resolve().parents[2] / "config")
            url = os.environ.get("AUTH_DB_PATH") and f"sqlite:///{os.environ['AUTH_DB_PATH']}" or database_url(cfg)
            cls.repo = CredentialRepository(open_store("memory://" if url == "sqlite:///:memory:" else url))
            cls.tokens, cls.box = TokenService.from_env(), SecretBox.from_env()
        return cls


def role_of(ctx, user_id: str) -> str:
    row = ctx.read.accepted_one(ACCESS_TABLE, user_id)
    return str((row or {}).get("role") or Roles.of(ctx.cfg).member)


CHALLENGE_HOURS = 5 / 60


def accept_session(ctx, cred, second_step_done: bool = False, remember: bool | None = None) -> None:
    """Issue the sealed access token for a verified person (password or provider login). With two-step login on, the
    first step only earns a 5-minute challenge; LOGIN_CODE turns it into a session once the app's code matches."""
    deps = Deps.get()
    if cred.two_step and not second_step_done:
        challenge = deps.tokens.issue({"sub": cred.user_id, "remember": bool(ctx.get("remember", False) if remember is None else remember)}, hours=CHALLENGE_HOURS, kind="two_step")
        return ctx.accept({"password_enc": "", "id_token_enc": "", "two_step": True, "registered": True,
                           "challenge_enc": deps.box.seal(challenge)})
    role = role_of(ctx, cred.user_id)
    remember = bool(ctx.get("remember", False)) if remember is None else remember
    hours = session_hours(Roles.of(ctx.cfg).is_staff(role), remember)
    token = deps.tokens.issue({"sub": cred.user_id, "role": role, "tenant": cred.tenant_id}, hours=hours)
    ctx.accept({"password_enc": "", "id_token_enc": "", "user_id": cred.user_id, "role": role, "expires_hours": hours,
                "token_enc": deps.box.seal(token), "registered": True,
                "two_step": False, "challenge_enc": "", "code": ""})


def provider_identity(ctx):
    """(Identity, None) from the request's provider + sealed id token, or (None, reason) to reject with."""
    provider = PROVIDERS.get(ctx.text("provider"))
    if provider is None:
        return None, "UNKNOWN_PROVIDER"
    settings = {**os.environ, **{k: v for k, v in open_settings(ctx.read.accepted(gc.settings.APP_SETTINGS)).items() if v}}
    if not provider.configured(settings):
        return None, "PROVIDER_NOT_CONFIGURED"
    try:
        return provider.verify(Deps.get().box.open(ctx.text("id_token_enc")), settings), None
    except IdentityError:
        return None, "INVALID_TOKEN"
